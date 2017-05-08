define([
  "components/vue/dist/vue",
  "jsapi/v1/resources"
], function(Vue, resources) {
  "use strict";
  return {
    template:
      '<modal-dialog>' +
      '    <div class="modal-header"><h4>Remove Accounting</h4></div>' +
      '    <div class="modal-body">Do you want to remove accounting {{ accToRemove.id }}?</div>' +
      '    <div class="modal-footer text-right">' +
      '          <div class="alert alert-danger" v-if="communicationError">' +
      '            <strong>Error:</strong> {{communicationError}}' +
      '          </div>' +
      '        <button type="button" class="btn btn-default" @click="close">Cancel</button>' +
      '        <button class="btn btn-primary primary" @click="removeAccounting">Remove</button>' +
      '    </div>' +
      '</modal-dialog>',
    props: ['accToRemove'],
    data: function() {
      return {
        communicationError: null
      };
    },
    methods: {
      close: function () {
        this.$emit("closed");
      },
      removeAccounting: function () {
        if (this.accToRemove.id === null) {
          this.$emit("closed");
          return;
        }
        resources.Accounting.delete(this.accToRemove.id)
          .done((function () {
            this.$emit("removed");
          }).bind(this))
          .fail(
            (function () {
              this.communicationError = "The request could not be executed successfully";
            }).bind(this)
          );
      }
    }
  };
});
