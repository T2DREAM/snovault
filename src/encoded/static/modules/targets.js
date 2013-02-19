define(['exports', 'jquery', 'underscore', 'base', 'table_sorter', 'table_filter',
    'text!templates/targets/home.html',
    'text!templates/targets/item.html',
    'text!templates/targets/row.html'],
function targets(exports, $, _, base, table_sorter, table_filter, home_template, item_template, row_template) {

    exports.Target = base.Model.extend({
        urlRoot: '/targets/',
        initialize: function initialize(attrs, options) {
            if (options && options.route_args) {
                this.id = options.route_args[0];
                this.deferred = this.fetch();
            }
        }
    });

    exports.TargetCollection = base.Collection.extend({
        model: exports.Target,
        url: '/targets/'
    });

    exports.TargetRowView = base.RowView.extend(
    {
        template: _.template(row_template)
    });

    // The targets home screen
    var targetHomeView = base.TableView.extend({
        row: exports.TargetRowView,
        template: _.template(home_template)
    },
    {
        route_name: 'targets',
        model_factory: exports.TargetCollection
    });

    var targetView = exports.TargetView = base.View.extend({
        initialize: function initialize(options) {
            var model = options.model;
            this.deferred = model.deferred;
        },
        template: _.template(item_template)
    }, {
        route_name: 'target',
        model_factory: exports.Target
    });

    return exports;
});
