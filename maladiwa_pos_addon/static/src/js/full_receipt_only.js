import { patch } from '@web/core/utils/patch';
import { PrintPopup } from '@point_of_sale/app/components/popups/print_popup/print_popup';

patch(PrintPopup.prototype, {
  get printList() {
    const options = super.printList;

    if (!this.pos.config.maladiwa_receipt_enabled) {
      return options;
    }

    // Odoo prints directly when only one option remains.
    return options.filter((option) => option.isPrimary);
  },
});
