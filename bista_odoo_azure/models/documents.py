from odoo import fields, models, api, tools, _

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import re
import base64
from datetime import datetime
import io
from time import strptime
import pdfkit
import unicodedata
import random


class DocumentsDocument(models.Model):
    _inherit = "documents.document"

    blank_invoice_created = fields.Boolean("Blank Invoice Created", default=False)

    def _find_match(self, key, string):
        return re.compile(r'\b({0})\b'.format(key), flags=re.IGNORECASE).search(string)

    def message_new(self, msg_dict, custom_values=None):
        if custom_values.get('create_share_id'):
            share_id = self.env['documents.share'].browse(custom_values['create_share_id'])
            if share_id.filter_mail:
                is_needed = False
                if share_id.filter_type_selection == 'sender':
                    from_string = msg_dict.get('email_from')
                    result = re.search('<(.*)>', from_string)

                    if result:
                        partner_email = result.group(1)
                    else:
                        partner_email = 'kjgkdjbdiqh3pe2e32e3we2q32e65216'
                    partner_email_id = self.env["res.partner.email"].search(['|', ("email", "=ilike", partner_email),
                                                                             ("email", "=ilike", from_string)],
                                                                            limit=1)
                    if partner_email_id.id:
                        is_needed = True

                elif share_id.filter_type_selection == 'attachment':
                    filters = share_id.mapped('filter_attachments.filter_name')
                else:
                    filters = share_id.mapped('filter_keywords.filter_name')
                    subject = msg_dict.get('subject')
                    content = tools.html2plaintext(msg_dict.get('body'))
                    for keyword in filters:
                        if self._find_match(keyword, subject):
                            is_needed = True
                            break
                        elif self._find_match(keyword, content):
                            is_needed = True
                            break
                if is_needed:
                    return super(DocumentsDocument, self).message_new(msg_dict, custom_values)
        return self

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, message_type='notification', **kwargs):
        if self:
            return super(DocumentsDocument, self).message_post(message_type=message_type, **kwargs)
        return False

    @api.model
    def _message_post_after_hook(self, message, msg_vals):
        res = super(DocumentsDocument, self)._message_post_after_hook(message, msg_vals)

        share = self.create_share_id

        if share:
            email_from_list = tools.email_normalize(msg_vals.get('email_from'))
            email_list = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+",
                                    email_from_list)
            email_from_list = email_list[0]
            partner_email_id = self.env["res.partner.email"].search([("email", "=ilike", email_from_list)], limit=1)
            if partner_email_id:
                result = unicodedata.normalize('NFKD', msg_vals.get('body'))
                pdf = pdfkit.from_string(result, False)
                attachment_name = str(partner_email_id.partner_id.name or '') + '_' + str(
                    random.randint(1000, 9999)) + '.pdf'
                attachment = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'type': 'binary',
                    'datas': base64.encodebytes(pdf),
                    'mimetype': 'application/pdf',
                })
                document = self.env['documents.document'].create({
                    'name': attachment.name,
                    'attachment_id': attachment.id,
                    'folder_id': share.folder_id.id,
                    'partner_id': partner_email_id.partner_id.id,
                })
                attachment.write({
                    'res_model': 'documents.document',
                    'res_id': document.id,
                })
        return res

    def _azure_doc_connector(self):
        company_id = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
        azure_endpoint = company_id.azure_end_point
        azure_key = company_id.azure_key
        azureDocObj = DocumentAnalysisClient(endpoint=azure_endpoint,
                                             credential=AzureKeyCredential(azure_key))

        return azureDocObj

    def _azure_doc_parser(self, result):

        final_result = {}
        for idx, document in enumerate(result.documents):
            for name, field in document.fields.items():
                field_value = field.value if field.value else field.content
                final_result.update({
                    name: field_value
                })
        tracking_number = final_result['Tracking Number']
        tracking_number_items = []
        if tracking_number:
            for index, data in enumerate(tracking_number):
                item_dict = {}
                vals = data.to_dict().get('value')
                item_dict.update({
                    'Item Number': index + 1,
                    'Tracking Id': vals.get('Tracking Id').get('value') if vals.get('Tracking Id') else False,
                })
                tracking_number_items.append(item_dict)
        if tracking_number_items:
            final_result.update({
                'Tracking Number': tracking_number_items
            })

        isbns = final_result['Line Item']
        isbns_item = []
        if isbns:
            for index, data in enumerate(isbns):
                item_dict = {}
                vals = data.to_dict().get('value')
                item_dict.update({
                    'Item Number': index + 1,
                    'ISBN': vals.get('ISBN').get('value') if vals.get('ISBN') else False,
                    'Quantity': vals.get('Quantity').get('value') if vals.get('Quantity') else False,
                })
                isbns_item.append(item_dict)
        if isbns_item:
            final_result.update({
                'Line Item': isbns_item
            })
        return final_result

    def _azure_doc_handler(self):
        log_name = str(datetime.now())

        try:
            azure_comm = self._azure_doc_connector()
        except Exception as e:
            log_html = """
            <h4> Connection Issue  : %s </h4>
            """ % e
            log = self.env['documents.azure.log'].create({
                "name": log_name,
                "log": log_html,
            })
            return False
        to_create_folder = self.env.ref('bista_odoo_azure.to_create_folder')
        unntrained_pdf_folder = self.env.ref('bista_odoo_azure.untrained_pdf')

        document_ids = self.search([
            ('partner_id', '!=', False),
            ('attachment_id', '!=', False),
            ('folder_id', '=', to_create_folder.id), ], limit=5)
        log_html = """
        <table>
            <thead>
                <tr>
                    <th style="width:33%;">File name</th>
                    <th style="width:33%;">Status</th>
                    <th style="width:33%;">Description</th>
                </tr>
            </thead>
            <tbody>
        """
        for document in document_ids:
            doc_name = str(document.name)
            if str(doc_name[-3:]) == 'pdf' or str(doc_name[-3:]) == 'PDF':
                pass
            else:
                filter_out_folder = self.env.ref('bista_odoo_azure.filtered_out_folder')
                document.update({
                    "folder_id": filter_out_folder.id,
                })
                tr = """
                                     <tr>
                                        <td>%s</td>
                                        <td>Finished</td>
                                        <td>Not a PDF</td>
                                     </tr>
                                                """ % (doc_name)
                log_html += tr
                continue
            data = base64.b64decode(document.attachment_id.datas)
            if document.partner_id.azuremodel_id:
                azure_model = document.partner_id.azuremodel_id.azure_model or \
                              self.company_id.azure_model
            else:
                document.update({
                    "folder_id": unntrained_pdf_folder.id,
                })
                tr = """
                     <tr>
                        <td>%s</td>
                        <td>Not Parsed</td>
                        <td> Model Not Set for the Vendor: %s</td>
                     </tr>
                                """ % (doc_name, document.partner_id.name)
                log_html += tr
                continue

            result = None

            with io.BytesIO(data) as file:
                try:
                    poller = azure_comm.begin_analyze_document(
                        model_id=azure_model, document=file)
                    result = poller.result()
                except Exception as e:
                    document.update({
                        "folder_id": unntrained_pdf_folder.id,
                    })
                    tr = """
                                         <tr>
                                            <td>%s</td>
                                            <td>Not Parsed</td>
                                            <td>%s</td>
                                         </tr>
                                                    """ % (doc_name, e)
                    log_html += tr
            if not result:
                continue
            parsed_data = self._azure_doc_parser(result)
            try:
                tracking = document._run_script(parsed_data, document)
            except Exception as e:
                tr = """
                <tr>
                    <td>%s</td>
                    <td>Not Finished</td>
                    <td>%s</td>
                </tr>
                """ % (doc_name, e)
                log_html += tr
                not_found_folder = self.env.ref('bista_odoo_azure.not_found_folder')
                document.update({
                    "folder_id": not_found_folder.id,
                })
            else:
                tr = """
                         <tr>
                            <td>%s</td>
                            <td>Finished</td>
                            <td>Bill name : %s</td>
                         </tr>
                                    """ % (doc_name, tracking.order_id.name)
                log_html += tr
                document.unlink()

        log_html += """
        </tbody>
        </table>
        """

        log = self.env['documents.azure.log'].create({
            "name": log_name,
            "log": log_html,
        })

    def _run_script(self, parsed_data, document):
        if parsed_data.get('PO Number'):
            po_number = parsed_data.get('PO Number')
            purchase_order_name = po_number.replace("(Reference", "")
            purchase_order = self.env['purchase.order'].search([('name', '=', purchase_order_name)])
            if purchase_order.id:
                if len(purchase_order.ids) == 0:
                    raise Exception("Purchase Order not found: ", purchase_order_name)
                elif len(purchase_order.ids) != 1:
                    raise Exception("Multiple Purchase Order found: ", purchase_order_name)

        if parsed_data.get('Carrier Name'):
            carrier = self.env['delivery.carrier'].search([('name', '=', parsed_data.get('Carrier Name'))])
            if carrier.ids:
                if len(carrier.ids) == 0:
                    raise Exception("Carrier not found: ", parsed_data.get('Carrier Name'))
                elif len(carrier.ids) != 1:
                    raise Exception("Multiple Carrier found: ", parsed_data.get('Carrier Name'))

        if parsed_data.get('Ship Date'):
            date = self._date_converter(parsed_data.get('Ship Date'))

        tracking_ref_ids_list = []
        if parsed_data.get('Tracking Number'):
            track_list = []
            tracking_number_list = parsed_data.get('Tracking Number')
            for list in tracking_number_list:
                numbers = list.get('Tracking Id')
                tracking_number = numbers.split(" ")
                for items in tracking_number:
                    final_item = ''
                    for char in items:
                        if char.isupper() or char.isdigit():
                            final_item = final_item + char
                    track_list.append(final_item)
            if len(track_list) > 0:
                for items in track_list:
                    tracking_ref_ids_list.append((0, 0, {
                        'name': items,
                    }))

        purchase_tracking_vals = {
            'order_id': purchase_order.id,
            'name': _("New"),
            'shipment_date': date,
            'carrier_id': carrier.id,
            'pro_number': parsed_data.get('Pro Number') or False,
            'tracking_ref_ids': tracking_ref_ids_list if len(tracking_ref_ids_list) > 0 else False,
        }

        tracking = self.env['purchase.tracking'].create(purchase_tracking_vals)
        if document.attachment_id:
            document.attachment_id.copy({
                'res_id': tracking.order_id.id,
                'res_model': 'purchase.order',
            })

        if parsed_data.get('Line Item'):
            isbn_list = parsed_data.get('Line Item')
            if len(isbn_list) > 0:
                tracking.onchange_order_id()
                if tracking.tracking_line_ids:
                    for isbns_line in isbn_list:
                        isbn_number = isbns_line.get('ISBN')
                        product_line = tracking.tracking_line_ids.filtered(
                            lambda p: p.default_code == isbn_number)
                        if len(product_line.ids) == 1:
                            product_line.ship_qty = self._strip_float(isbns_line.get('Quantity'))
                        else:
                            raise Exception("ISBN not found: ", isbn_number, " in PO: ", tracking.order_id.name)

        return tracking

    def _strip_float(self, value):
        p = '[\d]+|[\d]*[.][\d]+|[\d]+'
        final_val = ''
        if value:
            if re.search(p, value) is not None:
                for catch in re.finditer(p, value):
                    final_val = final_val + catch[0]

        return final_val

    def _date_converter(self, date_string):
        date_date = date_string
        sign = None

        for a in date_date:
            if (a.isspace()) == True:
                sign = " "
                break
            elif a == '/':
                sign = "/"
                break
            elif a == '-':
                sign = "-"
                break
        date_list = date_date.split(sign)
        date = self._get_date(date_list)
        return date

    def _get_date(self, date_list):
        if len(date_list[0]) == 4 and date_list[0].isdigit():
            year = date_list[0]
            el_0 = date_list[1]
            el_1 = date_list[-1]
        else:
            el_0 = date_list[0]
            el_1 = date_list[1]
            year = date_list[-1]
        day = None
        both_digit = False
        if any(a.isdigit() for a in el_0):
            day = el_0
            month = el_1
        if any(a.isdigit() for a in el_1):
            if day == None:
                day = el_1
                month = el_0
            else:
                both_digit = True
        if both_digit:
            if len(year) > 2:
                try:
                    date = datetime.strptime(el_0 + "/" + el_1 + "/" + year, '%m/%d/%Y').strftime('%Y-%m-%d')
                except:
                    date = datetime.strptime(el_1 + "/" + el_0 + "/" + year, '%m/%d/%Y').strftime('%Y-%m-%d')
            else:
                try:
                    date = datetime.strptime(el_0 + "/" + el_1 + "/" + year, '%m/%d/%y').strftime('%Y-%m-%d')
                except:
                    date = datetime.strptime(el_1 + "/" + el_0 + "/" + year, '%m/%d/%y').strftime('%Y-%m-%d')

            return date

        else:
            alpha_month = ''
            for a in month:
                if a.isalpha():
                    alpha_month = alpha_month + a
            if len(alpha_month) == 3:
                final_month = strptime(alpha_month, '%b').tm_mon
            else:
                final_month = strptime(alpha_month, '%B').tm_mon
            final_day = ''
            for a in day:
                if a.isdigit():
                    final_day = final_day + a

            final_date = final_day + "/" + str(final_month) + "/" + year
            if len(year) > 2:
                date = datetime.strptime(final_date, '%d/%m/%Y').strftime("%Y-%m-%d")
            else:
                date = datetime.strptime(final_date, '%d/%m/%y').strftime("%Y-%m-%d")

            return date
