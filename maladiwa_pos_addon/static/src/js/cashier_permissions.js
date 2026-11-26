import { patch } from '@web/core/utils/patch';
import { PosAccessRightPlugin } from '@point_of_sale/app/plugins/access_right_plugin';

patch(PosAccessRightPlugin.prototype, {
  get maladiwaCashier() {
    return Boolean(this.data.models['res.users'].getFirst()?.maladiwa_cashier);
  },

  get canAccessCustomerDisplay() {
    return !this.maladiwaCashier && super.canAccessCustomerDisplay;
  },

  get canInstallApp() {
    return !this.maladiwaCashier && super.canInstallApp;
  },

  get hasProductCreationAccess() {
    return !this.maladiwaCashier && super.hasProductCreationAccess;
  },

  get canGoToBackend() {
    return !this.maladiwaCashier && super.canGoToBackend;
  },

  get canCloseSession() {
    return !this.maladiwaCashier && super.canCloseSession;
  },
});
