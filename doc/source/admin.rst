Administrator screens
=====================

In this document we describe those Admin pages whose design and implementation
require additional elaboration.

TimeseriesFews
--------------

The Admin page for the TimeseriesFews model allows the user to select a time
series from the Fews unblobbed database. A time series in that database is
identified by three values, viz. a Parameter value, a Filter value and a
Location value. The default Admin page would contain an IntegerField for each
of those values but from a useability point-of-view, a ChoiceField would be
much better. For that reason, we have created a customized Admin form for
TimeseriesFews named TimeseriesFewsForm [#f1]_. The customized Admin form uses
a HTML SELECT control for each of the three values.

Unfortunately, the number of locations in a Fews unblobbed database can be
huge, e.g., in a test Fews unblobbed database there were 78.524 locations. The
retrieval of such an amount of locations and their subsequent storage in the
SELECT control would render the browser unresponsive for too long. Besides, you
can imagine the problem a user faces when he has to select one element from a
list of 78.524...

To work around this problem, we use the fact that once the user has selected
the Parameter and Filter values, the number of available locations is much
lower. So, we create an empty SELECT control for the locations. Then, as soon
as the user changes the Parameter or Filter selection, we dynamically fill that
control. The dynamic update of the locations SELECT control is implemented in
JavaScript [#f2]_.

.. [#f1] TimeseriesFewsForm can be found in lizard_waterbalance.forms.

.. [#f2] The JavaScript code can be found in lizard_waterbalance/templates/admin/lizard_waterbalance/timeseriesfews/change_form.html.
