odoo.define('signature_attachment_viewer.DocumentViewer', function (require) {
    "use strict";
    console.log("signature_attachment_viewer")

    var core = require('web.core');
    var Widget = require('web.Widget');


   var QWeb = core.qweb;

    var SCROLL_ZOOM_STEP = 0.1;
    var ZOOM_STEP = 0.5;

    var DocumentViewer = Widget.extend({
        template: "odx_DocumentViewer",
        events: {
            'click .o_download_btn': '_onDownload',
            'click .o_viewer_img': '_onImageClicked',
            'click .o_viewer_video': '_onVideoClicked',
            'click .move_next': '_onNext',
            'click .move_previous': '_onPrevious',
            'click .o_rotate': '_onRotate',
            'click .o_zoom_in': '_onZoomIn',
            'click .o_zoom_out': '_onZoomOut',
            'click .o_zoom_reset': '_onZoomReset',
            'click .o_close_btn, .o_viewer_img_wrapper': '_onClose',
            'click .o_print_btn': '_onPrint',
            'DOMMouseScroll .o_viewer_content': '_onScroll', // Firefox
            'mousewheel .o_viewer_content': '_onScroll', // Chrome, Safari, IE
            'keydown': '_onKeydown',
            'keyup': '_onKeyUp',
            'mousedown .o_viewer_img': '_onStartDrag',
            'mousemove .o_viewer_content': '_onDrag',
            'mouseup .o_viewer_content': '_onEndDrag',
             'click .o_save_pdf_with_signature': '_onSavePDFWithSignature',


        },






//_onSavePDFWithSignature: function (e) {
//    e.preventDefault();
//
//    var $sig = this.$('#signatureImg');
//    var $pdf = this.$('.o_viewer_pdf');
//    var $zoomer = this.$('.o_viewer_zoomer');
//
//    var offset = $sig.position();
//    var width = $sig.width();
//    var height = $sig.height();
//
//    var containerWidth = $zoomer.width();
//    var containerHeight = $zoomer.height();
//
//    // ✅ معرفة قيمة التمرير العمودي
//    var scrollTop = $zoomer.scrollTop();  // هذا هو ما تسأل عنه
//
//    // ✅ معرفة قيمة التمرير الأفقي (لو احتجته)
//    var scrollLeft = $zoomer.scrollLeft();
//
//    console.log('scrollTop',offset.top )
//        console.log('scrollLeft',scrollLeft)
//
//    var page = 1;
//    var data = {
//        pdf_attachment_id: this.activeAttachment.id,
//        signature_base64: $sig.attr('src').split(',')[1],
//        left: offset.left,
//        top: offset.top,
//        width: width,
//        height: height,
//        container_width: containerWidth,
//        container_height: containerHeight,
//        page_number: page,
//    };

//    this._rpc({
//        model: 'ir.attachment',
//        method: 'merge_signature_to_pdf',
//        args: [data],
//    }).then(function (result) {
//    window.open(result.download_url, '_blank');
//        // result = { download_url: ... }
////        if (result && result.download_url) {
////            window.open(result.download_url, "_blank");
////        } else {
////            alert("حدث خطأ في دمج التوقيع");
////        }
//    });
//},






        /**
         * The documentViewer takes an array of objects describing attachments in
         * argument, and the ID of an active attachment (the one to display first).
         * Documents that are not of type image or video are filtered out.
         *
         * @override
         * @param {Array<Object>} attachments list of attachments
         * @param {integer} activeAttachmentID
         */
        init: function (parent, attachments, activeAttachmentID,signature,record_id) {
            this._super.apply(this, arguments);
              this.record_id = record_id; // ✅ أصبح معرف الآن ويمكن استخدامه

        console.log('record_id:', this.record_id);

            this.signature = signature;
                console.log("DocumentViewer signature in init:", this.signature);

            this.attachment = _.filter(attachments, function (attachment) {
                var match = attachment.type === 'url' ? attachment.url.match("(youtu|.png|.jpg|.gif)") : attachment.mimetype.match("(image|video|application/pdf|text)");
                if (match) {
                    attachment.fileType = match[1];
                    if (match[1].match("(.png|.jpg|.gif)")) {
                        attachment.fileType = 'image';
                    }
                    if (match[1] === 'youtu') {
                        var youtube_array = attachment.url.split('/');
                        var youtube_token = youtube_array[youtube_array.length - 1];
                        if (youtube_token.indexOf('watch') !== -1) {
                            youtube_token = youtube_token.split('v=')[1];
                            var amp = youtube_token.indexOf('&');
                            if (amp !== -1) {
                                youtube_token = youtube_token.substring(0, amp);
                            }
                        }
                        attachment.youtube = youtube_token;
                    }
                    return true;
                }
            });
            this.activeAttachment = _.findWhere(attachments, { id: activeAttachmentID });
            this.modelName = 'ir.attachment';
            this._reset();
        },

        /**
         * Open a modal displaying the active attachment
         * @override
         */
        start: function () {



            this.$el.modal('show');
            this.$el.on('hidden.bs.modal', _.bind(this._onDestroy, this));
            this.$('.o_viewer_img').on("load", _.bind(this._onImageLoaded, this));
            this.$('[data-toggle="tooltip"]').tooltip({ delay: 0 });
            setTimeout(function() {
                if (window.$ && $("#signatureImg").length) {
                    $("#signatureImg").draggable({
                        containment: ".o_viewer_zoomer"
                    });
                }
            }, 300);

            return this._super.apply(this, arguments);
        },
        /**
         * @override
         */
        destroy: function () {
            if (this.isDestroyed()) {
                return;
            }
            this.trigger_up('document_viewer_closed');
            this.$el.modal('hide');
            this.$el.remove();
            this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //---------------------------------------------------------------------------

        /**
         * @private
         */
        _next: function () {
            var index = _.findIndex(this.attachment, this.activeAttachment);
            index = (index + 1) % this.attachment.length;
            this.activeAttachment = this.attachment[index];
            this._updateContent();
        },
        /**
         * @private
         */
        _previous: function () {
            var index = _.findIndex(this.attachment, this.activeAttachment);
            index = index === 0 ? this.attachment.length - 1 : index - 1;
            this.activeAttachment = this.attachment[index];
            this._updateContent();
        },
        /**
         * @private
         */
        _reset: function () {
            this.scale = 1;
            this.dragStartX = this.dragstopX = 0;
            this.dragStartY = this.dragstopY = 0;
        },
        /**
         * Render the active attachment
         *
         * @private
         */
        _updateContent: function () {
            this.$('.o_viewer_content').html(QWeb.render('odx.DocumentViewer.Content', {
                widget: this
            }));
            this.$('.o_viewer_img').on("load", _.bind(this._onImageLoaded, this));
            this.$('[data-toggle="tooltip"]').tooltip({ delay: 0 });
            this._reset();
        },
        /**
         * Get CSS transform property based on scale and angle
         *
         * @private
         * @param {float} scale
         * @param {float} angle
         */
        _getTransform: function (scale, angle) {
            return 'scale3d(' + scale + ', ' + scale + ', 1) rotate(' + angle + 'deg)';
        },
        /**
         * Rotate image clockwise by provided angle
         *
         * @private
         * @param {float} angle
         */
        _rotate: function (angle) {
            this._reset();
            var new_angle = (this.angle || 0) + angle;
            this.$('.o_viewer_img').css('transform', this._getTransform(this.scale, new_angle));
            this.$('.o_viewer_img').css('max-width', new_angle % 180 !== 0 ? $(document).height() : '100%');
            this.$('.o_viewer_img').css('max-height', new_angle % 180 !== 0 ? $(document).width() : '100%');
            this.angle = new_angle;
        },
        /**
         * Zoom in/out image by provided scale
         *
         * @private
         * @param {integer} scale
         */
        _zoom: function (scale) {
            if (scale > 0.5) {
                this.$('.o_viewer_img').css('transform', this._getTransform(scale, this.angle || 0));
                this.scale = scale;
            }
            this.$('.o_zoom_reset').add('.o_zoom_out').toggleClass('disabled', scale === 1);
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent} e
         */
        _onClose: function (e) {
            e.preventDefault();
            this.destroy();
        },
        /**
         * When popup close complete destroyed modal even DOM footprint too
         *
         * @private
         */
        _onDestroy: function () {
            this.destroy();
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onDownload: function (e) {
            e.preventDefault();
            window.location = '/web/content/' + this.modelName + '/' + this.activeAttachment.id + '/' + 'datas' + '?download=true';
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onDrag: function (e) {
            e.preventDefault();
            if (this.enableDrag) {
                var $image = this.$('.o_viewer_img');
                var $zoomer = this.$('.o_viewer_zoomer');
                var top = $image.prop('offsetHeight') * this.scale > $zoomer.height() ? e.clientY - this.dragStartY : 0;
                var left = $image.prop('offsetWidth') * this.scale > $zoomer.width() ? e.clientX - this.dragStartX : 0;
                $zoomer.css("transform", "translate3d(" + left + "px, " + top + "px, 0)");
                $image.css('cursor', 'move');
            }
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onEndDrag: function (e) {
            e.preventDefault();
            if (this.enableDrag) {
                this.enableDrag = false;
                this.dragstopX = e.clientX - this.dragStartX;
                this.dragstopY = e.clientY - this.dragStartY;
                this.$('.o_viewer_img').css('cursor', '');
            }
        },
        /**
         * On click of image do not close modal so stop event propagation
         *
         * @private
         * @param {MouseEvent} e
         */
        _onImageClicked: function (e) {
            e.stopPropagation();
        },
        /**
         * Remove loading indicator when image loaded
         * @private
         */
        _onImageLoaded: function () {
            this.$('.o_loading_img').hide();
        },
        /**
         * Move next previous attachment on keyboard right left key
         *
         * @private
         * @param {KeyEvent} e
         */
        _onKeydown: function (e) {
            switch (e.which) {
                case $.ui.keyCode.RIGHT:
                    e.preventDefault();
                    this._next();
                    break;
                case $.ui.keyCode.LEFT:
                    e.preventDefault();
                    this._previous();
                    break;
            }
        },
        /**
         * Close popup on ESCAPE keyup
         *
         * @private
         * @param {KeyEvent} e
         */
        _onKeyUp: function (e) {
            switch (e.which) {
                case $.ui.keyCode.ESCAPE:
                    e.preventDefault();
                    this._onClose(e);
                    break;
            }
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onNext: function (e) {
            e.preventDefault();
            this._next();
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onPrevious: function (e) {
            e.preventDefault();
            this._previous();
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onPrint: function (e) {
//            e.preventDefault();
            var src = this.$('.o_viewer_img').prop('src');
            var script = QWeb.render('odx.DocumentViewer.Content', {
                src: src
            });
            var printWindow = window.open('about:blank', "_new");
            printWindow.document.open();
            printWindow.document.write(script);
            printWindow.document.close();
//             e.preventDefault();
//            var src = this.$('.o_viewer_img').prop('src');
//            var script = QWeb.render('odx.DocumentViewer.Content', {
//                src: src
//            });
//            var printWindow = window.open('about:blank', "_new");
//            printWindow.document.open();
//            printWindow.document.write(script);
//            printWindow.document.close();
//                ev.stopPropagation();
//                this._print();
        },
        /**
         * Zoom image on scroll
         *
         * @private
         * @param {MouseEvent} e
         */
        _onScroll: function (e) {
            var scale;
            if (e.originalEvent.wheelDelta > 0 || e.originalEvent.detail < 0) {
                scale = this.scale + SCROLL_ZOOM_STEP;
                      console.log('scale +',scale);

                this._zoom(scale);
            } else {
                scale = this.scale - SCROLL_ZOOM_STEP;
                console.log('scale -',scale);
                this._zoom(scale);
            }
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onStartDrag: function (e) {
            e.preventDefault();
            this.enableDrag = true;
            this.dragStartX = e.clientX - (this.dragstopX || 0);
            this.dragStartY = e.clientY - (this.dragstopY || 0);
        },
        /**
         * On click of video do not close modal so stop event propagation
         * and provide play/pause the video instead of quitting it
         *
         * @private
         * @param {MouseEvent} e
         */
        _onVideoClicked: function (e) {
            e.stopPropagation();
            var videoElement = e.target;
            if (videoElement.paused) {
                videoElement.play();
            } else {
                videoElement.pause();
            }
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onRotate: function (e) {
            e.preventDefault();
            this._rotate(90);
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onZoomIn: function (e) {
            e.preventDefault();
            var scale = this.scale + ZOOM_STEP;
            console.log("rote")
            this._zoom(scale);
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onZoomOut: function (e) {
            e.preventDefault();
            var scale = this.scale - ZOOM_STEP;
            this._zoom(scale);
        },
        /**
         * @private
         * @param {MouseEvent} e
         */
        _onZoomReset: function (e) {
            e.preventDefault();
            this.$('.o_viewer_zoomer').css("transform", "");
            this._zoom(1);
        },

        _onSavePDFWithSignature: function (e) {
    e.preventDefault();

    var self = this;
    var $iframe = this.$('.o_viewer_pdf');
    var iframeWindow = $iframe[0].contentWindow;

    var interval = setInterval(() => {
        if (iframeWindow && iframeWindow.PDFViewerApplication && iframeWindow.PDFViewerApplication.pdfViewer) {
            clearInterval(interval);

            var currentPage = iframeWindow.PDFViewerApplication.pdfViewer.currentPageNumber;

            var iframeWidth = $iframe.width();
            var iframeHeight = $iframe.height();

            var pdfViewer = iframeWindow.PDFViewerApplication.pdfViewer;
            var currentPageNumber = pdfViewer.currentPageNumber;
            var pageView = pdfViewer.getPageView(currentPageNumber - 1);



            var $sig = self.$('#signatureImg');
            var width = $sig.width();
            var height = $sig.height();


var pageView = iframeWindow.PDFViewerApplication.pdfViewer.getPageView(currentPage - 1);
var pageDiv = $(pageView.div);

var pageOffset = pageDiv.offset();
var sigOffset = $sig.offset();

var sigWidth = $sig.width();
var sigHeight = $sig.height();

var relativeLeft = sigOffset.left - pageOffset.left;
var relativeTop = sigOffset.top - pageOffset.top;

relativeLeft = relativeLeft;
relativeTop = relativeTop;

relativeTop -= sigHeight * 0.5;
// ولو يمين كثير؟ نقص من اليسار:
relativeLeft -= sigWidth * 0.6;

console.log("✅ raw pos:", relativeLeft, relativeTop);

var positionLeftPercent = relativeLeft / pageView.width;
var positionTopPercent = relativeTop / pageView.height;

            var data = {
                pdf_attachment_id: self.activeAttachment.id,
                signature_base64: $sig.attr('src').split(',')[1],
    left: positionLeftPercent * pageView.width,
    top: positionTopPercent * pageView.height,
    width: $sig.width(),
    height: $sig.height(),
    container_width: pageView.width,
    container_height: pageView.height,
                page_number: currentPage,
                record_id : self.record_id,
            };

            var selfff = this;

            self._rpc({
                model: 'ir.attachment',
                method: 'merge_signature_to_pdf',
                args: [data],
            }).then(function (result) {
            window.location.reload();

            });

        }
    }, 200);
},


    });
    return DocumentViewer;
    });