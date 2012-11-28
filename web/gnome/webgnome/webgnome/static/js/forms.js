
define([
    'jquery',
    'lib/underscore',
    'lib/backbone',
    'models',
    'util',
    'lib/moment',
], function($, _, Backbone, models, util) {

    var ModalFormViewContainer = Backbone.View.extend({
        initialize: function() {
            _.bindAll(this);
            this.options.ajaxForms.on(models.AjaxForm.SUCCESS, this.refresh);
            this.formViews = {};
        },

        /*
         Refresh all forms from the server.

         Called when any `AjaxForm` on the page has a successful submit, in case
         additional forms should appear for new items.
         */
        refresh: function() {
            var _this = this;

            $.ajax({
                type: 'GET',
                url: this.options.url,
                tryCount: 0,
                retryLimit: 3,
                success: function(data) {
                    if (_.has(data, 'html')) {
                        _this.$el.html(data.html);
                        _this.trigger(ModalFormViewContainer.REFRESHED);
                    }
                },
                error: util.handleAjaxError
            });
        },

        formIdChanged: function(newId, oldId) {
            this.formViews[newId] = this.formViews[oldId];
            delete this.formViews[oldId];
        },

        add: function(opts, obj) {
            if (typeof opts === "number" || typeof opts === "string") {
                this.formViews[opts] = obj;
                return;
            }

            if (typeof opts === "object" &&
                    (_.has(opts, 'id') && opts.id)) {
                var view = new ModalFormView(opts);
                this.formViews[opts.id] = view;
                view.on(ModalFormView.ID_CHANGED, this.formIdChanged);
                return;
            }

            throw "Must pass ID and object or an options object.";
        },

        get: function(formId) {
            return this.formViews[formId];
        },

        deleteAll: function() {
            var _this = this;
             _.each(this.formViews, function(formView, key) {
                formView.remove();
                delete _this.formViews[key];
            });
        }
    }, {
        REFRESHED: 'modalFormViewContainer:refreshed'
    });


    /*
     `ModalFormView` is responsible for displaying HTML forms retrieved
     from and submitted to the server using an `AjaxForm object. `ModalFormView`
     displays an HTML form in a modal "window" over the page using the rendered HTML
     returned by the server. It listens to 'change' events on a bound `AjaxForm` and
     refreshes itself when that event fires.

     The view is designed to handle multi-step forms implemented purely in
     JavaScript (and HTML) using data- properties on DOM elements. The server
     returns one rendered form, but may split its content into several <div>s, each
     with a `data-step` property. If a form is structured this way, the user of the
     JavaScript application will see it as a multi-step form with "next," "back"
     and (at the end) a "save" or "create" button (the label is given by the server,
     but whatever it is, this is the button that signals final submission of the
     form).

     Submitting a form from `ModalFormView` serializes the form HTML and sends it to
     a bound `AjaxForm` model object, which then handles settings up the AJAX
     request for a POST.
     */
    var ModalFormView = Backbone.View.extend({
        initialize: function() {
            _.bindAll(this);
            this.$container = $(this.options.formContainerEl);
            this.ajaxForm = this.options.ajaxForm;
            this.ajaxForm.on(models.AjaxForm.CHANGED, this.ajaxFormChanged);
            this.setupEventHandlers();
        },

        /*
         Bind listeners to the form container using `on()`, so they persist if
         the underlying form elements are replaced.
         */
        setupEventHandlers: function() {
            this.id = '#' + this.$el.attr('id');
            this.$container.on('click', this.id + ' .btn-primary', this.submit);
            this.$container.on('click', this.id + ' .btn-next', this.goToNextStep);
            this.$container.on('click', this.id + ' .btn-prev', this.goToPreviousStep);
        },

        ajaxFormChanged: function(ajaxForm) {
            var formHtml = ajaxForm.form_html;
            if (formHtml) {
                this.refresh(formHtml);
                this.show();
            }
        },

        /*
         Hide any other visible modals and show this one.
         */
        show: function() {
            $('div.modal').modal('hide');
            this.$el.modal();
        },

        /*
         Reload this form's HTML by initiating an AJAX request via this view's
         bound `AjaxForm`. If the request is successful, this `ModelFormView` will
         fire its `ajaxFormChanged` event handler.
         */
        reload: function(id) {
            this.ajaxForm.get({id: id});
        },

        getForm: function() {
            return this.$el.find('form');
        },

        getFirstTabWithError: function() {
            if (this.getForm().find('.nav-tabs').length === 0) {
                return null;
            }

            var errorDiv = $('div.control-group.error').first();
            var tabDiv = errorDiv.closest('.tab-pane');

            if (tabDiv.length) {
                return tabDiv.attr('id');
            }
        },

        getFirstStepWithError: function() {
            var step = 1;

            if (!this.getForm().hasClass('multistep')) {
                return null;
            }

            var errorDiv = $('div.control-group.error').first();
            var stepDiv = errorDiv.closest('div.step');

            if (stepDiv === false) {
                step = stepDiv.attr('data-step');
            }

            return step;
        },

        getStep: function(stepNum) {
            return this.getForm().find('div[data-step="' + stepNum  + '"]').length > 0;
        },

        previousStepExists: function(stepNum) {
           return this.getStep(stepNum - 1);
        },

        nextStepExists: function(stepNum) {
            stepNum = parseInt(stepNum, 10);
            return this.getStep(stepNum + 1);
        },

        goToStep: function(stepNum) {
            var $form = this.getForm();

            if (!$form.hasClass('multistep')) {
                return;
            }

            var stepDiv = $form.find('div.step[data-step="' + stepNum + '"]');

            if (stepDiv.length === 0) {
                return;
            }

            var otherStepDivs = $form.find('div.step');
            otherStepDivs.addClass('hidden');
            otherStepDivs.removeClass('active');
            stepDiv.removeClass('hidden');
            stepDiv.addClass('active');

            var prevButton = this.$container.find('.btn-prev');
            var nextButton = this.$container.find('.btn-next');
            var saveButton = this.$container.find('.btn-primary');

            if (this.previousStepExists(stepNum)) {
                prevButton.removeClass('hidden');
            } else {
                prevButton.addClass('hidden');
            }

            if (this.nextStepExists(stepNum)) {
                nextButton.removeClass('hidden');
                saveButton.addClass('hidden');
                return;
            }

            nextButton.addClass('hidden');
            saveButton.removeClass('hidden');
        },

        goToNextStep: function() {
            var $form = this.getForm();

            if (!$form.hasClass('multistep')) {
                return;
            }

            var activeStepDiv = $form.find('div.step.active');
            var currentStep = parseInt(activeStepDiv.attr('data-step'), 10);
            this.goToStep(currentStep + 1);
        },

        goToPreviousStep: function(event) {
            var $form = this.getForm();

            if (!$form.hasClass('multistep')) {
                return;
            }

            var activeStep = $form.find('div.step.active');
            var currentStep = parseInt(activeStep.attr('data-step'), 10);
            this.goToStep(currentStep - 1);
        },

        submit: function(event) {
            event.preventDefault();
            var $form = this.getForm();
            this.ajaxForm.submit({
                data: $form.serialize(),
                url: $form.attr('action')
            });
            this.hide();
            return false;
        },

        /*
         Replace this form with the form in `html`, an HTML string rendered by the
         server. Recreate any jQuery UI datepickers on the form if necessary.
         If there is an error in the form, load the step with errors.
         */
        refresh: function(html) {
            var oldId = this.$el.attr('id');

            this.remove();

            var $html = $(html);
            $html.appendTo(this.$container);

            this.$el = $('#' + $html.attr('id'));

             // Setup datepickers
            _.each(this.$el.find('.date'), function(field) {
                $(field).datepicker({
                    changeMonth: true,
                    changeYear: true
                });
            });

            var stepWithError = this.getFirstStepWithError();
            if (stepWithError) {
                this.goToStep(stepWithError);
            }

            var tabWithError = this.getFirstTabWithError();
            if (tabWithError) {
                $('a[href="#' + tabWithError + '"]').tab('show');
            }

            this.setupEventHandlers();
            util.fixModals();

            var newId = this.$el.attr('id');
            if (oldId !== newId) {
                this.trigger(ModalFormView.ID_CHANGED, newId, oldId);
            }
        },

        hide: function() {
            this.$el.modal('hide');
        },

        remove: function() {
            this.hide();
            this.$el.empty();
            this.$el.remove();
            this.$container.off('click', this.id + ' .btn-primary', this.submit);
            this.$container.off('click', this.id + ' .btn-next', this.goToNextStep);
            this.$container.off('click', this.id + ' .btn-prev', this.goToPreviousStep);
        }
    }, {
        ID_CHANGED: 'modalFormView:idChanged'
    });


    /*
     This is a non-AJAX-enabled modal form object to support the "add mover" form,
     which asks the user to choose a type of mover to add. We then use the selection
     to disply another, more-specific form.
     */
    var AddMoverFormView = Backbone.View.extend({
        initialize: function() {
            _.bindAll(this);
            this.$container = $(this.options.formContainerEl);

            // Bind listeners to the container, using `on()`, so they persist.
            this.id = '#' + this.$el.attr('id');
            this.$container.on('click', this.id + ' .btn-primary', this.submit);
        },

        getForm: function() {
            return this.$el.find('form');
        },

        show: function() {
            this.$el.modal();
        },

        hide: function() {
            this.$el.modal('hide');
        },

        submit: function(event) {
            event.preventDefault();
            var $form = this.getForm();
            var moverType = $form.find('select[name="mover_type"]').val();

            if (moverType) {
                this.trigger(AddMoverFormView.MOVER_CHOSEN, moverType);
            }

            return false;
        }
    }, {
        // Events
        MOVER_CHOSEN: 'addMoverFormView:moverChosen'
    });


    /*
     `WindMoverFormView` handles the WindMover form.
     */
    var WindMoverFormView = ModalFormView.extend({
        initialize: function(options) {
            var _this = this;

            this.constructor.__super__.initialize.apply(this, arguments);
            this.renderTimeTable();

            this.$container.on('change', this.id + ' .direction', function() {
                _this.toggleDegreesInput(this);
            });

            this.$container.on('click', this.id + ' .add-time', function(event) {
                event.preventDefault();
                _this.addTime();
            });

            this.$container.on('click', this.id + ' .icon-edit', function(event) {
                event.preventDefault();
                _this.showEditForm(this);
            });

            // TODO: Move into function
            this.$container.on('click', this.id + ' .cancel', function(event) {
                event.preventDefault();
                var form = $(this).closest('.time-form');
                form.addClass('hidden');
                _this.clearInputs(form);
                form.detach().appendTo('.times-list');
                $('.add-time-form').find('.time-form').removeClass('hidden');
            });

            // TODO: Move into function
            this.$container.on('click', this.id + ' .save', function(event) {
                event.preventDefault();
                var $form = $(this).closest('.time-form');
                $form.addClass('hidden');
                // Delete the "original" form that we're replacing.
                $form.data('form-original').detach().empty().remove();
                $form.detach().appendTo('.times-list');
                $('.add-time-form').find('.time-form').removeClass('hidden');
                _this.getTimesTable().append($form);
                _this.renderTimeTable();
            });

            this.$container.on('click', this.id + ' .icon-trash', function(event) {
                event.preventDefault();
                var $form = $(this).closest('tr').data('data-form');
                $form.detach().empty().remove();
                _this.renderTimeTable();
            });
        },
        
        getTimesTable: function() {
            return this.$el.find('.time-list');           
        },

        showEditForm: function(editIcon) {
            var $form = $(editIcon).closest('tr').data('data-form');
            var addFormContainer = $('.add-time-form');
            var addTimeForm = addFormContainer.find('.time-form');
            addTimeForm.addClass('hidden');
            var $formCopy = $form.clone().appendTo(addFormContainer);
            $formCopy.data('form-original', $form);
            $formCopy.removeClass('hidden');
        },

        toggleDegreesInput: function(directionInput) {
            var $dirInput = $(directionInput);
            var selected_direction = $dirInput.val();
            var $formDiv = $dirInput.closest('.time-form');
            var $degreesControl = $formDiv.find(
                '.direction_degrees').closest('.control-group');

            if (selected_direction === 'Degrees true') {
                $degreesControl.removeClass('hidden');
            } else {
                $degreesControl.addClass('hidden');
            }
        },

        clearInputs: function(form) {
            $(form).find(':input').each(function() {
                $(this).val('').removeAttr('checked');
            });
        },

        /*
         Clone the add time form and add an item to the table of time series.
         */
        addTime: function() {
            var $addForm = this.$el.find('.add-time-form').find('.time-form');
            var $newForm = $addForm.clone(true).addClass('hidden');
            var formId = $addForm.find(':input')[0].id;
            var formNum = parseInt(formId.replace(/.*-(\d{1,4})-.*/m, '$1')) + 1;

            // There are no edit forms, so this is the first time series.
            if (!formNum) {
                formNum = 0;
            }

            // Select all of the options selected on the original form.
            _.each($addForm.find('select option:selected'), function(opt) {
                var $opt = $(opt);
                var name = $opt.closest('select').attr('name');
                var $newOpt = $newForm.find(
                    'select[name="' + name + '"] option[value="' + $opt.val() + '"]');
                $newOpt.attr('selected', true);
            });

            // Increment the IDs of the add form elements -- it should always be
            // the last form in the list of edit forms.
            $addForm.find(':input').each(function() {
                var id = $(this).attr('id');
                if (id) {
                    id = id.replace('-' + (formNum - 1) + '-', '-' + formNum + '-');
                    $(this).attr({'name': id, 'id': id});
                }
            });

            $newForm.find('.add-time-buttons').addClass('hidden');
            $newForm.find('.edit-time-buttons').removeClass('hidden');

            this.getTimesTable().after($newForm);
            this.renderTimeTable();

            var autoIncrementBy = $addForm.find('.auto_increment_by').val();

            // Increase the date and time on the Add form if 'auto increase by'
            // value was provided.
            if (autoIncrementBy) {
                var $date = $addForm.find('.date');
                var $hour = $addForm.find('.hour');
                var $minute = $addForm.find('.minute');
                var time = $hour.val()  + ':' + $minute.val();

                // TODO: Handle a date-parsing error here.
                var dateTime = moment($date.val() + ' ' + time);
                dateTime.add('hours', autoIncrementBy);

                $date.val(dateTime.format("MM/DD/YYYY"));
                $hour.val(dateTime.hours());
                $minute.val(dateTime.minutes());
            }
        },

        renderTimeTable: function() {
            var _this = this;
            var $forms = this.$el.find('.edit-time-forms').find('.time-form');
            var rows = [];

            // Clear out any existing rows.
            this.getTimesTable().find('tr').not('.table-header').remove();

            _.each($forms, function(form) {
                var $form = $(form);
                var tmpl = _.template($("#time-series-row").html());
                var speedType = $form.find('.speed_type option:selected').val();
                var direction = $form.find('.direction').val();

                if (direction === 'Degrees true') {
                    direction = $form.find('.direction_degrees').val() + ' &deg;';
                }

                var error = $form.find('span.help').length > 0;

                var dateTime = moment(
                    $form.find('.date').val() + ' ' +
                    $form.find('.hour').val() + ':' +
                    $form.find('.minute').val());

                rows.push($(tmpl({
                    error: error ? 'error' : '',
                    date: dateTime.format('MM/DD/YYYY'),
                    time: dateTime.format('HH:mm'),
                    direction: direction,
                    speed: $form.find('.speed').val() + ' ' + speedType
                })).data('data-form', $form));
            });

            // Sort table by date and time of each item.
            rows = _.sortBy(rows, function($tr) {
                var date = $tr.find('.time-series-date').text();
                var time = $tr.find(
                    '.time-series-time').text().replace(' ', '', 'g');
                return Date.parse(date + ' ' + time)
            });

            _.each(rows, function($row) {
                $row.appendTo(_this.getTimesTable());
            });
        },

        /*
         Remove the "Add" form inputs and submit the form.
         */
        submit: function() {
            this.$el.find('.add-time-form .time-form').empty().remove();
            WindMoverFormView.__super__.submit.apply(this, arguments);
        },

        ajaxFormChanged: function() {
            WindMoverFormView.__super__.ajaxFormChanged.apply(this, arguments);
            this.renderTimeTable();

            var hasErrors = this.$el.find(
                '.time-list').find('tr.error').length > 0;

            if (hasErrors) {
                alert('At least one of your time series values had errors in ' +
                     'it. The rows with values will be marked in red.');
            }
        }
    });

     return {
        AddMoverFormView: AddMoverFormView,
        WindMoverFormView: WindMoverFormView,
        ModalFormView: ModalFormView,
        ModalFormViewContainer: ModalFormViewContainer
    };

});