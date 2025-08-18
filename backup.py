import streamlit as st
import pandas as pd 


conn = st.connection("sql")
conteudos = conn.query('SELECT "id","title","moduleId" FROM public."Content";')
#subscriptions = conn.query('SELECT "userId" FROM public."Subscription";')
#freeContent = conn.query('SELECT "moduleId","contentId" FROM public."OfferAccess" WHERE "offerId" = 3;')
raw_views = conn.query('''SELECT "createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', CASE WHEN "totalViews" > 10 THEN 10 ELSE "totalViews" END AS "totalViews","contentId","userId" FROM public."ContentView" WHERE "totalViews" != 0;''')
#modulos = conn.query('SELECT "id","name","createdAt" FROM public."Module";')

views = []
raw_views = raw_views.sort_values(by="timezone", ascending=True)

for row in raw_views.itertuples():
    frcView = 0
    pacView = 0
    sfrView = 0
    spaView = 0
    ufrView = 0

    if conteudos[conteudos.id == row.contentId].moduleId.values[0] in freeContent.moduleId.values or row.contentId in freeContent.contentId.values:
        frcView = row.totalViews
    else:
        pacView = row.totalViews
        
    if row.userId not in subscriptions.userId.values:
        ufrView = row.totalViews
    else:
        if conteudos[conteudos.id == row.contentId].moduleId.values[0] in freeContent.moduleId.values or row.contentId in freeContent.contentId.values:
            sfrView = row.totalViews
        else:
            spaView = row.totalViews

    if row.contentId not in [item["contentId"] for item in views]:
        views.append({
            "contentId": row.contentId,
            "moduleId": conteudos[conteudos.id == row.contentId].moduleId.values[0],
            "totalViews": row.totalViews,
            "freeContentView":frcView,
            "paidContentView":pacView,
            "subFreeContentView": sfrView,
            "subPaidContentView": spaView,
            "unsubFreeContentView": ufrView,
            "viewedAt": [{str(row.timezone)[0:10] : row.totalViews}]
            })
    else:
        for item in views:
            if item["contentId"] == row.contentId:
                item["totalViews"] += row.totalViews
                item["freeContentView"] += frcView
                item["paidContentView"] += pacView
                item["unsubFreeContentView"] += ufrView
                item["subFreeContentView"] += sfrView
                item["subPaidContentView"] += spaView
                if str(row.timezone)[0:10] not in [list(view.keys())[0] for view in item["viewedAt"]]:
                    item["viewedAt"].append({str(row.timezone)[0:10] : row.totalViews})
                else:
                    for view in item["viewedAt"]:
                        if list(view.keys())[0] == str(row.timezone)[0:10]:
                            view[str(row.timezone)[0:10]] += row.totalViews
                            


views = pd.DataFrame(views)

tabelaContent = []
tabelaModule = []

for row in views.itertuples():
    if row.contentId in conteudos.id.values:
        tabelaContent.append({
            "title": conteudos[conteudos.id == row.contentId].title.values[0],
            "moduleId": row.moduleId,
            "moduleName": modulos[modulos.id == row.moduleId].name.values[0],
            "views": row.totalViews,
            "freeContentView":row.freeContentView,
            "paidContentView":row.paidContentView,
            "subFreeContentView":row.subFreeContentView,
            "subPaidContentView":row.subPaidContentView,
            "unsubFreeContentView":row.unsubFreeContentView,
            "viewedAt": row.viewedAt,
            "contentId": row.contentId
            })

tabelaContent = pd.DataFrame(tabelaContent)

for row in tabelaContent.itertuples():
    viewsDates = []
    freeViewsDates = []
    for obj in row.viewedAt:
        for item, date in obj.items():
            if item not in [list(view.keys())[0] for view in viewsDates]:
                viewsDates.append({
                    item: date
                })
            else:
                for view in viewsDates:
                    if list(view.keys())[0] == item:
                        view[item] += date

    if row.moduleId in modulos.id.values: 
        if row.moduleId not in [item["id"] for item in tabelaModule]:
            tabelaModule.append({
                "id": modulos[modulos.id == row.moduleId].id.values[0],
                "title": modulos[modulos.id == row.moduleId].name.values[0],
                "totalModuleViews": row.views,
                "freeContentView":row.freeContentView,
                "paidContentView":row.paidContentView,
                "subFreeContentView":row.subFreeContentView,
                "subPaidContentView":row.subPaidContentView,
                "unsubFreeContentView":row.unsubFreeContentView,
                "moduleViewedAt": viewsDates
            })
        else:
            for item in tabelaModule:
                if item["id"] == row.moduleId:
                    item["totalModuleViews"] += row.views
                    item["freeContentView"] += row.freeContentView
                    item["paidContentView"] += row.paidContentView
                    item["subFreeContentView"] += row.subFreeContentView
                    item["subPaidContentView"] += row.subPaidContentView
                    item["unsubFreeContentView"] += row.unsubFreeContentView
                    for view in viewsDates:
                        if list(view.keys())[0] not in [list(moduleView.keys())[0] for moduleView in item["moduleViewedAt"]]:
                            item["moduleViewedAt"].append(view)
                        else:
                            for moduleView in item["moduleViewedAt"]:
                                if list(moduleView.keys())[0] == list(view.keys())[0]:
                                    moduleView[list(view.keys())[0]] += list(view.values())[0]

tabelaModule = pd.DataFrame(tabelaModule)

st.title("Ranking de Módulos")
tabelaModule = tabelaModule.sort_values(by="totalModuleViews", ascending=False)
st.dataframe(tabelaModule, column_config={
    "id": None,
    "title": "Nome do Modulo",
    "totalModuleViews": "Total de Views",
    "moduleViewedAt": None,
    "freeContentView":None,
    "paidContentView":None,
    "subFreeContentView":None,
    "subPaidContentView":None,
    "unsubFreeContentView":None,
    
},
    hide_index=True,
)