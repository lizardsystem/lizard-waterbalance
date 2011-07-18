Inloggen op de website
======================

Als een gebruiker de pagina voor de waterbalansen opent, ziet hij een lijst van
waterbalans configuraties. Alleen van deze configuraties kan de gebruiker de
waterbalansen bekijken. Of een configuratie in die lijst staat of "zichtbaar"
is, wordt bepaald door een tweetal attributen van het scenario waar de
configuratie naar verwijst, namelijk "actief" en "publiek" [1]_.

Alleen als het scenario actief is, is de configuratie zichtbaar. Dat geldt voor
alle gebruikers inclusief Administrators. Is het scenario actief is en publiek,
dan is het zichtbaar voor alle gebruikers, ingelogd of niet. Is het scenario
actief maar niet-publiek, dan is het alleen zichtbaar voor gebruikers die
ingelogd zijn en het recht::

  lizard_waterbalance | Waterbalans scenario | Can see not public scenario's

hebben.

.. [1] Een waterbalans configuratie wordt geïmplementeerd door een
       WaterbalanceConf, een scenario door een WaterbalanceScenario.
