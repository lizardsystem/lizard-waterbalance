Zichtbaarheid configuraties
===========================

Als een gebruiker de pagina voor de waterbalansen opent, ziet hij een lijst van
waterbalans configuraties. Alleen van deze configuraties kan de gebruiker de
waterbalansen bekijken. Of een configuratie in die lijst staat of "zichtbaar"
is, wordt bepaald door het gebied en het scenario waar de configuratie naar
verwijst [1]_. Om in detail te gaan, de zichtbaarheid hangt af van het
attribuut "actief" van het gebied en van de attributen "actief" en "publiek"
van het scenario.

Alleen als het gebied én het scenario actief zijn, kan de configuratie
zichtbaar zijn. Dat geldt voor alle gebruikers inclusief Administrators. Zijn
beide actief en is het scenario ook nog publiek, dan is het zichtbaar voor alle
gebruikers, ingelogd of niet. Zijn beide actief maar is het scenario
niet-publiek, dan is het alleen zichtbaar voor gebruikers die ingelogd zijn en
het recht::

  lizard_waterbalance | Waterbalans scenario | Can see not public scenario's

hebben.

.. [1] Een waterbalans configuratie wordt geïmplementeerd door een
       WaterbalanceConf, een gebied door een WaterbalanceArea en een scenario
       door een WaterbalanceScenario.
