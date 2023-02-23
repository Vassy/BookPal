/** @odoo-module **/

import { registry } from "@web/core/registry";
var session = require('web.session');
var PreviewDialog = require("pdf_print_preview.PreviewDialog");


/**
 * Generates the report url given a report action.
 *
 * @private
 * @param {ReportAction} action
 * @returns {string}
 */
function _getReportUrl(action) {
    let url = `/report/pdf/${action.report_name}`;
    const actionContext = action.context || {};
    let filename = action.name;
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}&`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}?`;
        }
    }
    // if(filename !== undefined)
    //     filename = filename.replace(/[/?%#&=]/g, "") + ".pdf";
    return url //+= `${filename}`;
}

async function PdfPrintPreview(action, options, env) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
    const WKHTMLTOPDF_MESSAGES = {
        broken:
            env._t(
                "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                "in html."
            ) + link,
        install:
            env._t(
                "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
            ) + link,
        upgrade:
            env._t(
                "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                "get a correct display of headers and footers as well as support for " +
                "table-breaking between pages."
            ) + link,
        workers: env._t(
            "You need to start Odoo with at least two workers to print a pdf version of " +
            "the reports."
        ),
    };

    if (action.report_type === "qweb-pdf" && env.services.menu !== undefined) {
        let wkhtmltopdfStateProm = env.services.rpc("/report/check_wkhtmltopdf");
        const state = await wkhtmltopdfStateProm;

        // display a notification according to wkhtmltopdf's state
        if (state in WKHTMLTOPDF_MESSAGES) {
            env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                sticky: true,
                title: env._t("Report"),
            });
        }

        if (state === "upgrade" || state === "ok" && (session.preview_print || session.automatic_printing)) {
            let url = _getReportUrl(action);
            if (session.preview_print) {
                PreviewDialog.createPreviewDialog(self, url, action.name);
            }
            if (session.automatic_printing) {
                try {
                    var pdf = window.open(url);
                    pdf.print();
                }
                catch (err) {
                    env.services.notification.add(
                        env._t("Please allow pop up in your browser to preview report in another tab."),
                        {
                            sticky: true,
                            title: env._t("Report"),
                        });
                }
            }
            return true;
        }

    }

}

registry
    .category("ir.actions.report handlers")
    .add("pdf_print_preview", PdfPrintPreview);
