import logging

from lizard_map.adapter import Graph
from lizard_map.workspace import WorkspaceItemAdapter

logger = logging.getLogger(__name__)


class AdapterWaterbalance(WorkspaceItemAdapter):
    """Adapter for module LizardWaterbalance.

    Registered as adapter_waterbalance.

    Uses default database table "waterbalance_shape" as geo database.
    """

    def __init__(self, *args, **kwargs):
        super(AdapterWaterbalance, self).__init__(*args, **kwargs)
        self.shape_tablename = 'waterbalance_shape'

    def layer(self, layer_ids=None, request=None):
        """Return layer and styles for a parameter.
        """
        layers = []
        styles = {}
        return layers, styles

    def search(self, x, y, radius=None):
        results = []
        return results

    def symbol_url(self, identifier=None, start_date=None,
                   end_date=None, icon_style=None):
        """
        Returns symbol.
        """
        return super(AdapterWaterbalance, self).symbol_url()
            # identifier=identifier,
            # start_date=start_date,
            # end_date=end_date,
            # icon_style=icon_style)

    def location(self, parameter):
        result = []
        return result

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        return super(AdapterWaterbalance, self).html_default(
            snippet_group=snippet_group,
            identifiers=identifiers,
            layout_options=layout_options)

    def image(self, identifiers, start_date, end_date,
              width=380.0, height=250.0, layout_extra=None):

        today = datetime.datetime.now()
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)

        graph.add_today()
        return graph.http_png()

