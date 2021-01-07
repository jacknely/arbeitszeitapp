from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
from flask_table import LinkCol, Col
from . import db
from .models import Angebote, Kaeufe, Betriebe, Nutzer, PMVerbrauchGesamt, PMVerbrauchProdukt, Arbeit, Arbeiter
from .forms import ProductSearchForm
from .tables import ProduktionsmittelTable, ArbeiterTable
from decimal import Decimal
from sqlalchemy.sql.functions import coalesce

main_betriebe = Blueprint('main_betriebe', __name__)

@main_betriebe.route('/betriebe/home')
def index():
    try:
        user_type = session["user_type"]
    except:
        user_type = "betrieb"

    if user_type == "nutzer":
        return redirect(url_for('auth.zurueck'))
    else:
        session["user_type"] = "betrieb"
        return render_template('index_betriebe.html')

@main_betriebe.route('/betriebe/profile')
@login_required
def profile():
    user_type = session["user_type"]
    if user_type == "betrieb":
        return render_template('profile_betriebe.html')
    elif user_type == "nutzer":
        return redirect(url_for('auth.zurueck'))


@main_betriebe.route('/betriebe/arbeit', methods=['GET', 'POST'])
@login_required
def arbeit():
    arbeiter = db.session.query(Nutzer.id, Nutzer.name).select_from(Arbeiter)\
        .join(Nutzer, Arbeiter.nutzer==Nutzer.id).filter(Arbeiter.betrieb==current_user.id).all()
    table = ArbeiterTable(arbeiter, classes=["table", "is-bordered", "is-striped"])
    fik = Betriebe.query.filter_by(id=current_user.id).first().fik

    if request.method == 'POST':
        # check if nutzer exists, if not flash warning
        if not Nutzer.query.filter_by(id=request.form['nutzer']).first():
            flash("Nutzer existiert nicht.")
            return redirect(url_for('main_betriebe.arbeit'))

        # check if nutzer is already arbeiter in betrieb
        req_arbeiter = Arbeiter.query.filter_by(nutzer=request.form['nutzer'], betrieb=current_user.id).first()
        # if so, flash warning
        if req_arbeiter:
            flash("Nutzer ist bereits in diesem Betrieb beschäftigt.")
        else:
            new_arbeiter = Arbeiter(nutzer=request.form['nutzer'], betrieb=current_user.id)
            db.session.add(new_arbeiter)
            db.session.commit()
        return redirect(url_for('main_betriebe.arbeit'))

    return render_template("arbeit.html", table=table, fik=fik)

@main_betriebe.route('/betriebe/produktionsmittel')
@login_required
def produktionsmittel():
    produktionsmittel_qry = db.session.query(Kaeufe.id, Angebote.name, Angebote.beschreibung,\
        Angebote.preis, coalesce(PMVerbrauchGesamt.prozent_gebraucht, 0).label("prozent_gebraucht")).\
        outerjoin(Angebote, Kaeufe.angebot==Angebote.id).outerjoin(PMVerbrauchGesamt,\
        Kaeufe.id==PMVerbrauchGesamt.kauf).filter(Kaeufe.betrieb==current_user.id)

    produktionsmittel_aktiv = produktionsmittel_qry.filter(PMVerbrauchGesamt.prozent_gebraucht < 100).all()
    produktionsmittel_inaktiv = produktionsmittel_qry.filter(PMVerbrauchGesamt.prozent_gebraucht == 100).all()

    table_aktiv = ProduktionsmittelTable(produktionsmittel_aktiv, classes=["table", "is-bordered", "is-striped"])
    table_inaktiv = ProduktionsmittelTable(produktionsmittel_inaktiv, classes=["table", "is-bordered", "is-striped"])
    return render_template('produktionsmittel.html', table_aktiv=table_aktiv, table_inaktiv=table_inaktiv)


@main_betriebe.route('/betriebe/suchen', methods=['GET', 'POST'])
@login_required
def suchen():
    search = ProductSearchForm(request.form)
    if request.method == 'POST':
        results = []
        search_string = search.data['search']

        if search_string:
            if search.data['select'] == 'Name':
                qry = db.session.query(Angebote.id, Angebote.name, Betriebe.name,\
                    Angebote.beschreibung, Angebote.kategorie, Angebote.preis).select_from(Angebote).\
                    join(Betriebe, Angebote.betrieb==Betriebe.id).filter(Angebote.aktiv == True,\
                    Angebote.name.contains(search_string)).\
                    order_by(Angebote.id)
                results = qry.all()

            elif search.data['select'] == 'Beschreibung':
                qry = db.session.query(Angebote.id, Angebote.name, Betriebe.name,\
                    Angebote.beschreibung, Angebote.kategorie, Angebote.preis).select_from(Angebote).\
                    join(Betriebe, Angebote.betrieb==Betriebe.id).filter(Angebote.aktiv == True,\
                    Angebote.beschreibung.contains(search_string)).\
                    order_by(Angebote.id)
                results = qry.all()

            elif search.data['select'] == 'Kategorie':
                qry = db.session.query(Angebote.id, Angebote.name, Betriebe.name,\
                    Angebote.beschreibung, Angebote.kategorie, Angebote.preis).select_from(Angebote).\
                    join(Betriebe, Angebote.betrieb==Betriebe.id).filter(Angebote.aktiv == True,\
                    Angebote.kategorie.contains(search_string)).\
                    order_by(Angebote.id)
                results = qry.all()

            else:
                qry = db.session.query(Angebote.id, Angebote.name, Betriebe.name,\
                    Angebote.beschreibung, Angebote.kategorie, Angebote.preis).select_from(Angebote).\
                    join(Betriebe, Angebote.betrieb==Betriebe.id).filter(Angebote.aktiv == True).\
                    order_by(Angebote.id)
                results = qry.all()
        else:
            qry = db.session.query(Angebote.id, Angebote.name, Betriebe.name,\
                Angebote.beschreibung, Angebote.kategorie, Angebote.preis).select_from(Angebote).\
                join(Betriebe, Angebote.betrieb==Betriebe.id).filter(Angebote.aktiv == True).\
                order_by(Angebote.id)
            results = qry.all()

        if not results:
            flash('Keine Ergebnisse!')
            return redirect('/betriebe/suchen')
        else:
            return render_template('suchen_betriebe.html', form=search, results=results)

    return render_template('suchen_betriebe.html', form=search)



@main_betriebe.route('/betriebe/kaufen/<int:id>', methods=['GET', 'POST'])
def kaufen(id):
    qry = db.session.query(Angebote).filter(
                Angebote.id==id)
    angebot = qry.first()
    if angebot:
        if request.method == 'POST':
            # kauefe aktualisieren
            new_kauf = Kaeufe(angebot = angebot.id,
                    type_nutzer = False, betrieb = current_user.id,
                    nutzer = None)
            db.session.add(new_kauf)
            db.session.commit()
            # angebote aktualisieren (aktiv = False)
            angebot.aktiv = False
            db.session.commit()
            # produktionsmittel (Verbrauch Gesamt) aktualisieren
            new_produktionsmittel = PMVerbrauchGesamt(kauf=new_kauf.id, prozent_gebraucht=0)
            db.session.add(new_produktionsmittel)
            db.session.commit()
            # guthaben self aktualisieren
            kaufender_betrieb = db.session.query(Betriebe).filter(Betriebe.id == current_user.id).first()
            kaufender_betrieb.guthaben -= angebot.preis
            db.session.commit()
            # guthaben der arbeiter erhöhen
            arbeit_in_produkt = Arbeit.query.filter_by(angebot=angebot.id).all()
            print("u_u_u", arbeit_in_produkt)
            for arb in arbeit_in_produkt:
                Nutzer.query.filter_by(id=arb.nutzer).first().guthaben += arb.stunden
                arb.ausbezahlt = True
                db.session.commit()

            # guthaben des anbietenden betriebes erhöhen
            anbietender_betrieb_id = angebot.betrieb
            anbietender_betrieb = Betriebe.query.filter_by(id=anbietender_betrieb_id).first()
            anbietender_betrieb.guthaben += angebot.p_kosten

            # # guthaben des anbietenden betriebes verringern, wenn ausbezahlt = false
            # for arb in arbeit_in_produkt:
            #     anbietender_betrieb.guthaben -= arb.stunden
            #     db.session.commit()

            flash(f"Kauf von '{angebot.name}' erfolgreich!")
            return redirect('/betriebe/suchen')

        return render_template('kaufen_betriebe.html', angebot=angebot)
    else:
        return 'Error loading #{id}'.format(id=id)


@main_betriebe.route('/betriebe/anbieten_info', methods=['GET', 'POST'])
@login_required
def anbieten_info():
    """
    infos zum anbieten von produkten
    """

    return render_template('anbieten_info.html')



@main_betriebe.route('/betriebe/anbieten', methods=['GET', 'POST'])
@login_required
def neues_angebot():
    """
    Ein neues Angebot hinzufügen
    """
    produktionsmittel_aktiv = db.session.query(Kaeufe.id, Angebote.name, Angebote.beschreibung,\
        Angebote.preis, coalesce(PMVerbrauchGesamt.prozent_gebraucht, 0).label("prozent_gebraucht"), PMVerbrauchGesamt.id).\
        outerjoin(Angebote, Kaeufe.angebot==Angebote.id).outerjoin(PMVerbrauchGesamt,\
        Kaeufe.id==PMVerbrauchGesamt.kauf).filter(Kaeufe.betrieb==current_user.id, PMVerbrauchGesamt.prozent_gebraucht < 100).all()

    arbeiter_all = db.session.query(Nutzer.id, Nutzer.name).select_from(Arbeiter)\
        .join(Nutzer, Arbeiter.nutzer==Nutzer.id).filter(Arbeiter.betrieb==current_user.id).all()

    if request.method == 'POST':
        print("ubb", request.form)
        # create request dictionary
        request_dict = request.form.to_dict()

        # arbeit
        # dict with arbeit values
        arbeit_dict = dict(filter(lambda elem: elem[0][:7] == 'nutzer_', request_dict.items()))
        # arbeit dict entries that are not zero
        arbeit_dict_not_zero = dict(filter(lambda elem: Decimal(elem[1]) != 0, arbeit_dict.items()))
        kosten_arbeit = 0

        # produktionsmittel
        # dict with produktionsmittel values
        pm_dict = dict(filter(lambda elem: elem[0][:3] == 'id_', request_dict.items()))
        # pm dict entries that are not zero
        pm_dict_not_zero = dict(filter(lambda elem: Decimal(elem[1]) != 0,pm_dict.items()))
        kosten_pm = 0
        if pm_dict_not_zero:
            # calculate kosten pm
            id_list = []
            prozent_list = []
            for key in list(pm_dict_not_zero.keys()):
                id_list.append(key[3:])
            for value in list(pm_dict_not_zero.values()):
                prozent_list.append(Decimal(value)/100)
            # preise
            preise_list = []
            for idx in id_list:
                qry = db.session.query(Kaeufe, Angebote.preis).join(Angebote, Kaeufe.angebot==Angebote.id).filter(Kaeufe.id == idx).all()
                preise_list.append(Decimal(qry[0][1]))
            kosten_einzeln = []
            for num1, num2 in zip(prozent_list, preise_list):
                kosten_einzeln.append(num1 * num2)
            kosten_pm = sum(kosten_einzeln)
            # update prodmittel gebraucht (gesamt) in prozent
            assert len(id_list) == len(prozent_list)
            for count, i in enumerate(id_list):
                prdmittel = db.session.query(PMVerbrauchGesamt).filter(PMVerbrauchGesamt.kauf == i).first()
                prdmittel.prozent_gebraucht += prozent_list[count]*100
                db.session.commit()

        if arbeit_dict_not_zero:
            # calculate kosten arbeit
            nutzer_id_list = []
            stunden_list = []
            for key in list(arbeit_dict_not_zero.keys()):
                nutzer_id_list.append(key[7:])
            for value in list(arbeit_dict_not_zero.values()):
                stunden_list.append(Decimal(value))
            print(nutzer_id_list, stunden_list)
            assert len(nutzer_id_list) == len(stunden_list)
            kosten_arbeit = sum(stunden_list)

        # save new angebot
        new_angebot = Angebote(name=request.form["name"], betrieb=current_user.id,\
            beschreibung=request.form["beschreibung"], kategorie=request.form["kategorie"], p_kosten=kosten_pm,\
            v_kosten=kosten_arbeit, preis=kosten_arbeit + kosten_pm)
        db.session.add(new_angebot)
        db.session.commit()

        # create rows in prdmittel gebraucht (Produkt)
        if pm_dict_not_zero:
            assert len(id_list) == len(prozent_list)
            for count, i in enumerate(id_list):
                new_produktionsmittel_prd = PMVerbrauchProdukt\
                    (angebot=new_angebot.id, kauf=i, prozent_gebraucht=prozent_list[count]*100)
                db.session.add(new_produktionsmittel_prd)
                db.session.commit()

        # create rows in table "arbeit"
        if arbeit_dict_not_zero:
            assert len(nutzer_id_list) == len(stunden_list)
            for count, i in enumerate(nutzer_id_list):
                new_arbeit = Arbeit(angebot=new_angebot.id, nutzer=i,\
                    stunden=stunden_list[count], ausbezahlt=False)
                db.session.add(new_arbeit)
                db.session.commit()

        # kosten zusammenfassen und bestätigen lassen!
        flash('Angebot erfolgreich gespeichert!')
        return redirect('/betriebe/home')

    categ = ["Auto, Rad & Boot", "Dienstleistungen", "Eintrittskarten & Tickets", "Elektronik", "Familie, Kind & Baby",
    "Freizeit, Hobby & Nachbarschaft", "Haus & Garten", "Haustiere", "Immobilien", "Jobs", "Mode & Beauty", "Musik, Filme und Bücher",
    "Nachbarschaftshilfe", "Unterricht und Kurse", "Verschenken & Tauschen"]

    return render_template('neues_angebot.html', produktionsmittel_aktiv=produktionsmittel_aktiv, arbeiter_all=arbeiter_all, categ=categ)


@main_betriebe.route('/betriebe/meine_angebote')
@login_required
def meine_angebote():
    results = Angebote.query.filter_by(aktiv=True, betrieb=current_user.id).all()
    print("res", results)
    return render_template('meine_angebote.html', results=results)

@main_betriebe.route('/betriebe/angebot_loeschen', methods=['GET', 'POST'])
@login_required
def angebot_loeschen():
    angebot_id = request.args.get("id")
    angebot = Angebote.query.filter_by(id=angebot_id).first()

    if request.method == 'POST':
        if request.form["verbraucht"] == "ja":
            ...
        else:
            ...
        flash("gelöscht...")



    return render_template('angebot_loeschen.html', angebot=angebot)
