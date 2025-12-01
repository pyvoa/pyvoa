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
- [ ] Pas de variable indiquée sur les histos bokeh
- [ ] quand on sauve un bokeh, le logo disparait
- [ ] avec un pandas externe, obligation de charger une base avant. Ce qui est idiot.
- [ ] hist avec dateslider immonde. Exemple : pf.hist(where='métropole',which='tot_dchosp',typeofmap='dense',dateslider=True,when=':31/12/2020')
- [ ] SPF crash : pf.hist(where='métropole',which='tot_dchosp',dateslider=True,when=':31/12/2020',option=["normalize:pop1M","nonneg"])
OWID PBL : 
pf.map(dateslider=True,which='total_cases_per_million',when=':31/12/2020')
- [ ] dans les histos (au moins), on n'est pas à 20 caractères pour les lieux. Et il n'y a plus les " … " 
- [ ] mettre les puissances de 10 sur les abscisses (matplotlib et bokeh)
- [ ] problème de l'export png du bokeh : définition pourrie (screenshot meilleur)
- [ ] pour une spiral : pas de nom de variable tracé
- [ ] pour une spiral : pas de logo pyvoa en bokeh
- [ ] pas le même min / max avec et sans dateslider