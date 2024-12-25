odoo.define('size_restriction_for_attachments/static/src/js/file_uploader_size_restriction.js', function (require) {
    "use strict";

    const components  = {
        FileUploader: require("mail/static/src/components/file_uploader/file_uploader.js")  
    };

    const { patch } = require("web.utils");
    var session = require('web.session');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;

    patch(components.FileUploader,"size_restriction_for_attachments/static/src/js/file_uploader_size_restriction.js" ,{
        
        /**
         * using to set fileMaxSize variable on setup stage
         */
        setup () {
            this.fileMaxSize = 0;
            this._getMaxFileSize();
        },
        
        /**
         * get max file size from user restriction field
         */
        _getMaxFileSize: async function () {
            var self = this;

            await rpc.query({
                model: 'res.users',
                method: 'read',
                args: [[session.uid], ['set_restriction','max_size']],
            }).then(function (result) {

                if(result[0].set_restriction){
                    self.fileMaxSize = result[0].max_size * 1024 * 1024;
                }

            });
        },

        /**
         * @override
         */
        async uploadFiles(files) {
            var self = this;

            if(files.length > 0){
                for (const file of files) {
                    if (file.size > self.fileMaxSize) {
                        this.env.services["notification"].notify({
                            type: "danger",
                            message: owl.utils.escape(
                                _.str.sprintf(_t('The selected file exceeds the maximum file size of %s MB'),(self.fileMaxSize/1024/1024))
                            ),
                        });
                        return false;
                    }
                }
            }
            return this._super(files);
          },
        
    });

});