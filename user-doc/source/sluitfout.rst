Sluitfout
=========

De waterbalans app berekent de hoeveelheid water die per dag ingelaten dan wel
weggepompt moet worden om het waterpeil niet onder het minimum en niet boven
het maximum waterpeil te laten uitkomen. Dat noemen we peilhandhaving.

De gebruiker kan de kunstwerken definiëren die de app mag gebruiken voor
peilhandhaving [1]_. Ook kan hij voor die kunstwerken de gemeten hoeveelheid
water specificeren door tijdreeksen. Als de waterbalans app de peilhandhaving
berekent, dan negeert hij de gemeten tijdreeksen van de kunstwerken die voor
peilhandhaving gebruikt moeten worden. Het gaat er tenslotte om die tijdreeksen
zelf te bereken.

.. index:: single: sluitfout

De berekende tijdreeksen wijken waarschijnlijk af van de gemeten tijdreeksen en
dat verschil noemen we de sluitfout. De waterbalans grafiek toont de totale
sluitfout per door de gebruiker ingestelde tijdseenheid. De debieten voor de
berekende peilhandhaving worden niet getoond omdat de grafiek anders hetzelfde
debiet dubbel toont.

Let wel, de gebruiker is niet verplicht om gemeten tijdreeksen te definiëren
voor een kunstwerk dat gebruikt mag worden voor peilhandhaving. Zelfs is hij
niet verplicht om die kunstwerken te definiëren. Als ze ontbreken, zal de
waterbalans app ze aanmaken maar deze zijn dan niet zichtbaar voor de
gebruiker. Voor beide gevallen geldt dan dat de sluitfout gelijk is aan de
berekende tijdreeksen van de kunstwerken die gebruikt mogen worden voor
peilhandhaving.

.. [1] In de Admin is van een kunstwerk dat voor peilhandhaving gebruikt mag
       worden het attribuut "Berekend" aangevinkt.
