/** @odoo-module **/

import { registry } from "@web/core/registry";


function ReportPreviewItem(env) {
    return {
        type: "item",
        id: "report_preview",
        description: env._t("Report preview"),
        callback: async function () {
            const actionDescription = await env.services.rpc("/web/action/load", {
                action_id: "pdf_print_preview.action_short_preview_print"
            });
            actionDescription.res_id = env.services.user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 50,
    };
}

registry.category("user_menuitems").add("report_preview", ReportPreviewItem);
