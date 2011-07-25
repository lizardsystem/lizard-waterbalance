Managemant command import_excel
===============================

Het import script kijkt alleen naar de sheet "Uitgangspunten".

De namen van de inlaten staan in A24 tot en met A27. De namen van de uitlaten
staan in A28 tot en met A31. De in- en uitlaten die hier staan worden niet
gebruikt voor peilhandhaving.

Het script definieert altijd één inlaat voor peilhandhaving en één uitlaat voor
peilhandhaving met de namen "inlaat peilhandhaving" respectievelijk "uitlaat
peilhandhaving". Deze namen dien dan ook niet voor te komen voor de in- en
uitlaten die gedefinieerd worden in A24 tot en met A31.

E73, F73, G73 en H73 bevatten de namen van de pomplijnen voor de uitlaat voor
peilhandhaving. I73 bevat de pomplijn voor de inlaat voor peilhandhaving. K73
tot en met R73 bevatten de namen van de opgedrukte pomplijnen. Daarbij bevat
K73 de naam van de pomplijn van het kunstwerk waarvan de naam in A24 staat, L73
van het kunstwerk waarvan de naam in A25 staat enz.

Is bijvoorbeeld K73 leeg, dan dien B24 en C24 de winter en zomerstanden van de
tijdreeks te bevatten. We spreken dan van een jaarlijkse tijdreeks.
