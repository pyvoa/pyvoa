- [ ] virer warning sur dateutil (e.g. pour JHU-USA)
- [ ] virer warning sur geo_point_2d (e.g. pour SPF)
- [ ] seaborn : ralonger les noms coupés à 20 caractères
- [ ] seaborn : logo pyvoao limité à l'intérieur du rond du pie
- [ ] warning matplotlib avec map (spf, typeofmap dense) : The inferred zoom level of 22 is not valid for the current tile provider
- [ ] placer un logo pyvoa avec fond transparent (souci visible notamment avec hist )
- [ ] logo pyvoa trop gros avec matplotlib et seaborn
- [ ] ajouter les ":" après le nom de la base en capitale
- [ ] virer seaborn ? virer folium ? des visus dispo ? 
- [ ] bokeh, au niveau du curseur, des NaN s'affichent. e.g. avec spf / pf.plot(which='cur_rea',where="Ile-de-France",option='sumall',when='22/03/2020:28/03/2021')
- [ ] bokeh, aux environs du logo, on n'a pas de curseur donnant les résultats
- [ ] spf / sumall → légende "Ain, Aisne… → indiquer "sumall" ? ou "France" ? quand rien n'est précisé…
- [ ] souci sur l'axe des dates pour → pf.setwhom('jhu-usa',reload=False)
pf.plot(when='18/03/2020:01/04/2020',what='daily',which='tot_deaths',option='sumall')
- [ ] spf / pf.map(where='métropole',which='tot_dchosp',typeofmap='dense',dateslider=True,when=':31/12/2020') → pas de variable indiquée sur le graphe
- [ ] pbl avec le dateslider. 
Exemple 
pf.map(where='métropole',which='tot_dchosp',typeofmap='dense',dateslider=True,when=':31/12/2020') # d'une part
pf.map(where='métropole',which='tot_dchosp',typeofmap='dense',when='05/05/2020') # d'autre part → on n'obtient pas pareil.
- [ ] en bokeh / owid / pf.map(dateslider=True,when=':31/12/2020') # → quand on fait "play" les proportions changent !