import { patch } from '@web/core/utils/patch';
import { PosOrder } from '@point_of_sale/app/models/pos_order';
import { GeneratePrinterData } from '@point_of_sale/app/utils/printer/generate_printer_data';

patch(PosOrder.prototype, {
  setup() {
    super.setup(...arguments);

    const config = this.config;

    if (this.state === 'draft' && config.maladiwa_receipt_enabled) {
      this.maladiwa_usd_rate ||= config.maladiwa_usd_rate;

      this.maladiwa_service_product_id ||= config.maladiwa_service_product_id;

      this.maladiwa_service_percent ||= config.maladiwa_dine_in_preset_id?.service_fee_amount || 0;
    }
  },
});

patch(GeneratePrinterData.prototype, {
  generateReceiptData() {
    const data = super.generateReceiptData(...arguments);
    const config = this.config;

    if (!config.maladiwa_receipt_enabled || this.basicReceipt || this.simplified) {
      return data;
    }

    const order = this.order;
    const rate = order.maladiwa_usd_rate || config.maladiwa_usd_rate;

    if (!Number.isFinite(rate) || rate <= 0 || this.currency.name !== 'MVR') {
      throw new Error('Check the Maladiwa POS currency and USD rate in Settings.');
    }

    const product = order.maladiwa_service_product_id || config.maladiwa_service_product_id;

    const feeLines = order.lines.filter((line) => line.product_id.id === product?.id);

    const service = feeLines.reduce((sum, line) => sum + line.priceExcl, 0);

    const number = (value) => this.currency.round(value).toFixed(2);
    const total = order.totalDue;
    const rounding = total - order.priceIncl;

    data.extra_data.maladiwa = {
      subtotal: 'MVR ' + number(order.priceExcl - service),
      service: number(service),
      has_service: !this.currency.isZero(service),
      service_label: `${Number((order.maladiwa_service_percent * 100).toFixed(4))}% Service Charge`,
      gst: number(order.amountTaxes),
      total: 'MVR ' + number(total),
      usd: number(total / rate),
      rate: String(rate),
      change: 'MVR ' + number(order.amount_return || 0),
      rounding: number(rounding),
      has_rounding: !this.currency.isZero(rounding),
      reference: order.pos_reference || order.name,
      table: order.table_id ? String(order.table_id.table_number) : '',
      guests: order.customer_count || 0,
      is_refund: total < 0,
      items: order.lines
        .filter((line) => !feeLines.includes(line))
        .map((line) => ({
          id: line.uuid,
          name: line.getFullProductName(),
          qty: String(line.qty),
          amount: number(line.priceExcl),
          discount: String(line.discount || 0),
        })),
    };

    return data;
  },
});
