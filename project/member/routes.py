from decimal import Decimal
from flask import Blueprint, render_template, session,\
    redirect, url_for, request, flash
from flask_login import login_required, current_user
from project.tables import KaeufeTable, Preiszusammensetzung
from project.forms import ProductSearchForm
from project import database
from project.economy import member


main_member = Blueprint(
    'main_member', __name__, template_folder='templates',
    static_folder='static'
    )


@main_member.route('/member/kaeufe')
@login_required
def my_purchases():
    user_type = session["user_type"]

    if user_type == "company":
        return redirect(url_for('auth.zurueck'))
    else:
        session["user_type"] = "member"

        purchases = database.get_purchases(current_user.id)
        kaufh_table = KaeufeTable(purchases, no_items="(Noch keine Käufe.)")
        return render_template('member/my_purchases.html', kaufh_table=kaufh_table)


@main_member.route('/member/suchen', methods=['GET', 'POST'])
@login_required
def suchen():
    """search products in catalog."""
    search_form = ProductSearchForm(request.form)
    srch = database.SearchProducts()
    results = srch.get_active_offers()

    if request.method == 'POST':
        results = []
        search_string = search_form.data['search']
        search_field = search_form.data['select']  # Name, Beschr., Kategorie

        if search_string:
            results = srch.get_active_offers(search_string, search_field)
        else:
            results = srch.get_active_offers()

        if not results:
            flash('Keine Ergebnisse!')
        else:
            return render_template(
                'member/search.html', form=search_form, results=results)

    return render_template(
        'member/search.html', form=search_form, results=results)


@main_member.route('/member/details/<int:id>', methods=['GET', 'POST'])
@login_required
def details(id):
    """show details of selected product."""
    comp = database.CompositionOfPrices()
    table_of_composition = comp.get_table_of_composition(id)
    cols_dict = comp.get_positions_in_table(table_of_composition)
    dot = comp.create_dots(cols_dict, table_of_composition)
    piped = dot.pipe().decode('utf-8')
    table_preiszus = Preiszusammensetzung(table_of_composition)
    srch = database.SearchProducts()
    angebot_ = srch.get_offer_by_id(id)
    preise = (angebot_.preis, angebot_.koop_preis)

    if request.method == 'POST':
        return redirect('/member/suchen')

    return render_template(
        'member/details.html',
        table_preiszus=table_preiszus,
        piped=piped,
        preise=preise)


@main_member.route('/member/buy/<int:id>', methods=['GET', 'POST'])
@login_required
def buy(id):
    srch = database.SearchProducts()
    angebot = srch.get_offer_by_id(id)
    if request.method == 'POST':  # if user buys
        member.buy_product(
            "member", database.get_offer_by_id(id), current_user.id)
        flash(f"Kauf von '{angebot.angebot_name}' erfolgreich!")
        return redirect('/member/suchen')

    return render_template('member/buy.html', angebot=angebot)


@main_member.route('/member/profile')
@login_required
def profile():
    user_type = session["user_type"]
    if user_type == "member":
        workplaces = database.get_workplaces(current_user.id)
        return render_template('member/profile.html',
                               workplaces=workplaces)
    elif user_type == "company":
        return redirect(url_for('auth.zurueck'))


@main_member.route('/member/withdrawal', methods=['GET', 'POST'])
@login_required
def withdrawal():
    if request.method == 'POST':
        amount = Decimal(request.form["betrag"])
        code = member.withdraw(current_user.id, amount)
        # Show code to user
        flash(amount)
        flash(code)
        return render_template('member/withdrawal.html')

    return render_template('member/withdrawal.html')


@main_member.route('/member/hilfe')
@login_required
def hilfe():
    return render_template('member/help.html')
