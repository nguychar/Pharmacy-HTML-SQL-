# The code utilized for this web application draws inspiration from the code for the flask-starter-app
# made available through the learning Explorations.

from flask import Flask, render_template, json, redirect
from flask_mysqldb import MySQL
from flask import request
import os

app = Flask(__name__)

# database connection info

mysql = MySQL(app)

# Routes
@app.route("/")
def home():
    return redirect("/index")

@app.route('/index', methods=['GET','POST'])
def index():
    if request.method=="GET":
        drug_query = "SELECT drug_ndc AS 'NDC', CONCAT(drug_name, ' ', strength_in_mg, ' ', form) AS 'Drug', manufacturer AS 'Manufacturer', units_in_stock AS 'Quantity' FROM Drugs ORDER BY drug_name;"
        cur = mysql.connection.cursor()
        cur.execute(drug_query)
        data = cur.fetchall()

        pharmacist_query="SELECT rph_id, CONCAT (rph_first_name, ' ', rph_last_name) AS 'RPH' FROM Pharmacists Order BY rph_first_name;"
        cur = mysql.connection.cursor()
        cur.execute(pharmacist_query)
        rph_data = cur.fetchall()

        return render_template("index.j2",data=data, rph_data= rph_data)

    if request.method=="POST":
        if request.form.get("add_drug"):
            # grab user form inputs
            drug_ndc = request.form["drug_ndc"]
            drug_name = request.form["drug_name"]
            strength_in_mg = request.form["strength_in_mg"]
            form = request.form["form"]
            manufacturer = request.form["manufacturer"]
            is_generic = request.form["is_generic"]
	
            query = "INSERT INTO Drugs (drug_ndc, drug_name, strength_in_mg, form, manufacturer, is_generic) VALUES (%s, %s, %s, %s, %s, %s);"
            cur = mysql.connection.cursor()
            cur.execute(query, (drug_ndc, drug_name, strength_in_mg, form, manufacturer, is_generic))
            mysql.connection.commit()

            return redirect ('/index')

        if request.form.get("add_rx"):
            drug_ndc = request.form["drug_ndc"]
            date = request.form["date"]
            rph_id = request.form["rph_id"]
            if rph_id == "":
                rph_id = None
            quantity = request.form["rx_quantity"]
            price = request.form["price"]

            query2 = "INSERT INTO Prescriptions (drug_ndc, rx_date, rph_id, units_dispensed, rx_price) VALUES (%s, %s, %s, %s, %s);"
            cur = mysql.connection.cursor()
            cur.execute(query2, (drug_ndc, date, rph_id, quantity, price,))
            mysql.connection.commit()

            query3= "UPDATE Drugs SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s) WHERE Drugs.drug_ndc= %s;"
            cur = mysql.connection.cursor()
            cur.execute(query3, (drug_ndc, quantity, drug_ndc,))
            mysql.connection.commit()

            return redirect ('/index')

@app.route('/drug_audit/<int:drug_ndc>', methods=['GET','POST'])
def drugaudit(drug_ndc):
    if request.method=="GET":
        drug_query = "SELECT * FROM Drugs WHERE drug_ndc = %s;"
        cur = mysql.connection.cursor()
        cur.execute(drug_query, (drug_ndc,))
        drug_data = cur.fetchall()

        dispense_query = "SELECT Prescriptions.rx_date AS 'Date Dispensed', Prescriptions.rx_number AS 'Prescription Number', Prescriptions.units_dispensed AS 'Quantity Dispensed', CONCAT(Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'Rph' FROM Prescriptions LEFT JOIN Pharmacists ON Pharmacists.rph_id = Prescriptions.rph_id WHERE Prescriptions.drug_ndc = %s ORDER BY Prescriptions.rx_date;"
        cur = mysql.connection.cursor()
        cur.execute(dispense_query, (drug_ndc,))
        dispense_data = cur.fetchall()

        invoice_query="SELECT Invoices.order_date AS 'Invoice Date', Invoices.po_number AS 'PO Number', Distributors.distributor_name AS 'Distributor', Drugs_Has_Invoices.units_ordered AS 'Quantity Ordered' FROM Invoices LEFT JOIN Drugs_Has_Invoices ON Invoices.po_number = Drugs_Has_Invoices.po_number AND Drugs_Has_Invoices.drug_ndc = %s JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number WHERE Drugs_Has_Invoices.drug_ndc = %s;"
        cur = mysql.connection.cursor()
        cur.execute(invoice_query, (drug_ndc, drug_ndc,))
        invoice_data= cur.fetchall()

        return render_template("drugaudit.j2",dispense_data=dispense_data, invoice_data= invoice_data, drug_data=drug_data)

    if request.method=="POST":
        if request.form.get("update_drug"):
            # grab user form inputs
            drug_ndc = request.form["drug_ndc"]
            form = request.form["form"]
            manufacturer = request.form["manufacturer"]
            
            query = "UPDATE Drugs SET form = %s, manufacturer = %s WHERE drug_ndc = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (form, manufacturer, drug_ndc,))
            mysql.connection.commit()

            return redirect('/drug_audit/' + drug_ndc)

@app.route("/distributors", methods=["POST", "GET"])
def distributors():
    if request.method == "POST":
        if request.form.get("Add_Distributor"):
            name = request.form["name"]

            query = "INSERT INTO Distributors (distributor_name) VALUES (%s);"
            cur = mysql.connection.cursor()
            cur.execute(query, (name,))
            mysql.connection.commit()

            return redirect("/distributors")

    if request.method == "GET":
        query = "SELECT Distributors.distributor_number AS 'Number', Distributors.distributor_name AS 'Distributor Name', IFNULL(SUM(Invoices.order_cost), 0) AS 'Total Expenses' FROM Distributors LEFT JOIN Invoices ON Distributors.distributor_number = Invoices.distributor_number GROUP BY Distributors.distributor_number;"
        cur = mysql.connection.cursor()
        cur.execute(query)
        data = cur.fetchall()

        return render_template("distributors.j2", data=data)

@app.route("/delete_distributor/<int:id>")
def delete_distributor(id):
    query = "DELETE FROM Distributors WHERE distributor_number = '%s';"
    cur = mysql.connection.cursor()
    cur.execute(query, (id,))
    mysql.connection.commit()

    return redirect("/distributors")

@app.route("/edit_distributor/<int:id>", methods=["POST", "GET"])
def edit_distributor(id):
    if request.method == "GET":
        query = "SELECT Distributors.distributor_number, Distributors.distributor_name, IFNULL(SUM(Invoices.order_cost), 0) FROM Distributors LEFT JOIN Invoices ON Distributors.distributor_number = Invoices.distributor_number WHERE Distributors.distributor_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (id,))
        data = cur.fetchall()

        return render_template("edit_distributors.j2", data=data)

    if request.method == "POST":
        if request.form.get("Edit_Distributor"):
            name = request.form["name"]

            query = "UPDATE Distributors SET distributor_name = %s WHERE distributor_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (name, id))
            mysql.connection.commit()
            
            return redirect("/distributors")

@app.route("/transactions/<int:id>", methods=["GET", "POST"])
def transactions(id):
    if request.method == "POST":
        if request.form.get("Add_Transaction"):
            drug_ndc = request.form["drug_ndc"]
            quantity = request.form["quantity"]
            cost = request.form["cost"]
            po = request.form["po"]

            query = "INSERT INTO Drugs_Has_Invoices (drug_ndc, po_number, units_ordered, drug_subtotal) VALUES (%s, %s, %s, %s);"
            cur = mysql.connection.cursor()
            cur.execute(query, (drug_ndc, id, quantity, cost,))
            mysql.connection.commit()

            invoice_update = "UPDATE Invoices SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) + %s WHERE po_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(invoice_update, (id, cost, id,))
            mysql.connection.commit()

            drug_update = "UPDATE Drugs SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s WHERE drug_ndc = %s;"
            cur = mysql.connection.cursor()
            cur.execute(drug_update, (drug_ndc, quantity, drug_ndc,))
            mysql.connection.commit()

            return redirect("/transactions/" + po)

    if request.method == "GET":
        invoice_query = "SELECT * FROM Invoices WHERE po_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(invoice_query, (id,))
        invoice_data = cur.fetchall()

        distributor = invoice_data[0]['distributor_number']

        distributor_query = "SELECT distributor_name FROM Distributors WHERE distributor_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(distributor_query, (distributor,))
        distributor_data = cur.fetchall()

        drug_query = "SELECT CONCAT (drug_ndc, ' (', drug_name, ')') AS DRUG FROM Drugs;"
        cur = mysql.connection.cursor()
        cur.execute(drug_query)
        drug_data = cur.fetchall()

        query = "SELECT * FROM Drugs_Has_Invoices WHERE po_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (id,))
        data = cur.fetchall()

        return render_template("transactions.j2", invoice_data=invoice_data, distributor_data=distributor_data, drug_data=drug_data, data=data)

@app.route("/transactions/delete_transaction/<int:po>/<int:ndc>")
def delete_transaction(po, ndc):
    select_query = "SELECT * FROM Drugs_Has_Invoices WHERE po_number = %s and drug_ndc = %s;"
    cur = mysql.connection.cursor()
    cur.execute(select_query, (po, ndc,))
    data = cur.fetchall()

    quantity = data[0]['units_ordered']
    cost = data[0]['drug_subtotal']

    query = "DELETE FROM Drugs_Has_Invoices WHERE po_number = %s AND drug_ndc = %s;"
    cur = mysql.connection.cursor()
    cur.execute(query, (po, ndc,))
    mysql.connection.commit()

    invoice_query = "UPDATE Invoices SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) - %s WHERE po_number = %s;"
    cur = mysql.connection.cursor()
    cur.execute(invoice_query, (po, cost, po,))
    mysql.connection.commit()

    update_query = "UPDATE Drugs SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s WHERE drug_ndc = %s;"
    cur = mysql.connection.cursor()
    cur.execute(update_query, (ndc, quantity, ndc,))
    mysql.connection.commit()

    return redirect("/invoices")

@app.route("/transactions/edit_transaction/<int:po>/<int:ndc>", methods=["POST", "GET"])
def edit_transaction(po, ndc):
    if request.method == "GET":
        query = "SELECT * FROM Drugs_Has_Invoices WHERE po_number = %s and drug_ndc = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (po, ndc,))
        data = cur.fetchall()

        return render_template("edit_transactions.j2", data=data)

    if request.method == "POST":
        if request.form.get("Edit_Transaction"):
            quantity = request.form["quantity"]
            cost = request.form["cost"]
            po_number = request.form["po_number"]

            query = "UPDATE Drugs_Has_Invoices SET units_ordered = %s, drug_subtotal = %s WHERE drug_ndc = %s AND po_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (quantity, cost, ndc, po,))
            mysql.connection.commit()

            old_cost = request.form["old_cost"]
            old_quantity = request.form["old_quantity"]

            invoice_query = "UPDATE Invoices SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) + %s - %s WHERE po_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(invoice_query, (po, cost, old_cost, po,))
            mysql.connection.commit()

            update_query = "UPDATE Drugs SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s - %s WHERE drug_ndc = %s;"
            cur = mysql.connection.cursor()
            cur.execute(update_query, (ndc, quantity, old_quantity, ndc,))
            mysql.connection.commit()

            return redirect("/transactions/" + po_number)

@app.route("/invoices", methods=["POST", "GET"])
def invoices():
    if request.method == "POST":
        if request.form.get("Add_Invoice"):
            distributor = request.form["distributor"]
            date = request.form["date"]

            query = "INSERT INTO Invoices (distributor_number, order_date) VALUES ((SELECT distributor_number FROM Distributors WHERE distributor_name = %s), %s);"
            cur = mysql.connection.cursor()
            cur.execute(query, (distributor, date,))
            mysql.connection.commit()

            return redirect("/invoices")

    if request.method == "GET":
        query = "SELECT Invoices.po_number, Distributors.distributor_name AS 'Distributor', Invoices.order_date AS 'Order Date', IFNULL(SUM(Drugs_Has_Invoices.drug_subtotal), 0) AS 'Order Cost ($)' FROM Invoices JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number LEFT JOIN Drugs_Has_Invoices ON Drugs_Has_Invoices.po_number = Invoices.po_number GROUP BY Invoices.po_number ORDER BY Invoices.order_date DESC;"
        cur = mysql.connection.cursor()
        cur.execute(query)
        data = cur.fetchall()

        distributor_query = "SELECT * FROM Distributors;"
        cur = mysql.connection.cursor()
        cur.execute(distributor_query)
        distributor_data = cur.fetchall()

        return render_template("invoices.j2", data=data, distributor_data=distributor_data)

@app.route("/delete_invoice/<int:id>")
def delete_invoice(id):
    transaction_query = "SELECT * FROM Drugs_Has_Invoices WHERE po_number = %s;"
    cur = mysql.connection.cursor()
    cur.execute(transaction_query, (id,))
    transactions = cur.fetchall()

    for number in range(0, len(transactions)):
        ndc = transactions[number]['drug_ndc']
        units = transactions[number]['units_ordered']
        query = "UPDATE Drugs SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s WHERE drug_ndc = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (ndc, units, ndc,))
        mysql.connection.commit()

    query = "DELETE FROM Invoices WHERE po_number = '%s';"
    cur = mysql.connection.cursor()
    cur.execute(query, (id,))
    mysql.connection.commit()

    return redirect("/invoices")

@app.route("/edit_invoice/<int:id>", methods=["POST", "GET"])
def edit_invoice(id):
    if request.method == "GET":
        query = "SELECT Invoices.po_number, Distributors.distributor_name AS 'Distributor', Invoices.order_date AS 'Order Date', IFNULL(SUM(Drugs_Has_Invoices.drug_subtotal), 0) AS 'Order Cost ($)' FROM Invoices JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number LEFT JOIN Drugs_Has_Invoices ON Drugs_Has_Invoices.po_number = Invoices.po_number WHERE Invoices.po_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (id,))
        data = cur.fetchall()

        distributor_query = "SELECT * FROM Distributors;"
        cur = mysql.connection.cursor()
        cur.execute(distributor_query)
        distributor_data = cur.fetchall()

        return render_template("edit_invoices.j2", data=data, distributor_data = distributor_data)

    if request.method == "POST":
        if request.form.get("Edit_Invoice"):
            distributor = request.form["distributor"]
            date = request.form["date"]
            cost = request.form["cost"]

            query = "UPDATE Invoices SET distributor_number = (SELECT distributor_number FROM Distributors WHERE distributor_name = %s), order_date = %s, order_cost = %s WHERE po_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (distributor, date, cost, id))
            mysql.connection.commit()
            
            return redirect("/invoices")

@app.route('/pharmacists', methods=['GET','POST'])
def pharmacists():
    if request.method=="GET":
        query = "SELECT Pharmacists.rph_id, Pharmacists.rph_first_name AS 'First Name', Pharmacists.rph_last_name AS 'Last Name', COUNT(Prescriptions.rph_id) AS '# of C2s Processed' FROM Pharmacists LEFT JOIN Prescriptions ON Pharmacists.rph_id = Prescriptions.rph_id GROUP BY Pharmacists.rph_id;"
        cur = mysql.connection.cursor()
        cur.execute(query)
        data = cur.fetchall()

        return render_template("pharmacists.j2", data=data)

    if request.method=="POST":
        if request.form.get("add_rph"):
            # grab user form inputs
            fname = request.form["fname"]
            lname = request.form["lname"]
            query = "INSERT INTO Pharmacists (rph_first_name, rph_last_name) VALUES (%s, %s);"
            cur = mysql.connection.cursor()
            cur.execute(query, (fname, lname,))
            mysql.connection.commit()

            return redirect('/pharmacists')

@app.route("/delete_rph/<int:rph_id>")
def delete_rph(rph_id):
    # mySQL query to delete the person with our passed id
    query = "DELETE FROM Pharmacists WHERE rph_id = %s;"
    cur = mysql.connection.cursor()
    cur.execute(query, (rph_id,))
    mysql.connection.commit()

    return redirect('/pharmacists')

@app.route("/edit_rph/<int:rph_id>", methods=['GET','POST'])
     # mySQL query to delete the person with our passed id
def edit_rph(rph_id):
    if request.method== "GET":
        query = "SELECT * FROM Pharmacists WHERE rph_id = %s;"
        cur = mysql.connection.cursor()
        cur.execute(query, (rph_id,))
        data = cur.fetchall()
        
        return render_template("edit_pharmacists.j2", data=data)

    if request.method=="POST":
        if request.form.get("edit_rph"):
            # grab user form inputs
            fname = request.form["fname"]
            lname = request.form["lname"]
            rphid = request.form["rphid"]
            query = "UPDATE Pharmacists SET rph_first_name = %s, rph_last_name = %s WHERE rph_id = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (fname, lname, rphid))
            mysql.connection.commit()

            return redirect ('/pharmacists')

@app.route('/prescriptions', methods=['GET','POST'])
def prescriptions():
    if request.method=="GET":
        rx_query = "SELECT rx_number, rx_date AS 'Date', CONCAT(drug_name, ' ', strength_in_mg) AS 'Drug Dispensed', units_dispensed AS 'Quantity', CONCAT(Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'RPH' FROM Prescriptions JOIN Drugs ON Drugs.drug_ndc = Prescriptions.drug_ndc LEFT JOIN Pharmacists ON Prescriptions.rph_id = Pharmacists.rph_id ORDER BY Prescriptions.rx_date DESC;"
        cur = mysql.connection.cursor()
        cur.execute(rx_query)
        rx_data = cur.fetchall()

        return render_template("prescriptions.j2", rx_data=rx_data)

@app.route('/prescriptions/delete/<int:rx_number>')
def delete_rx(rx_number):
    drug_ndc_query = "SELECT drug_ndc, units_dispensed FROM Prescriptions WHERE rx_number = %s;"
    cur = mysql.connection.cursor()
    cur.execute(drug_ndc_query, (rx_number,))
    drug = cur.fetchall()
    update_ndc = drug[0]["drug_ndc"]
    update_quantity = drug[0]["units_dispensed"]

    rx_query = "DELETE FROM Prescriptions WHERE rx_number = %s;"
    cur = mysql.connection.cursor()
    cur.execute(rx_query, (rx_number,))
    mysql.connection.commit()

    #after deleting prescription, add the drug back into inventory
    update_query = "UPDATE Drugs SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s) WHERE drug_ndc = %s;"
    cur = mysql.connection.cursor()
    cur.execute(update_query, (update_ndc, update_quantity, update_ndc))
    mysql.connection.commit()

    return redirect('/prescriptions')

@app.route('/edit_prescription/<int:rx_number>', methods=['GET','POST'])
def edit_rx(rx_number):
    if request.method== "GET":
        rx_query = "SELECT * FROM Prescriptions WHERE rx_number = %s;"
        cur = mysql.connection.cursor()
        cur.execute(rx_query, (rx_number,))
        rx_data = cur.fetchall()

        rph_query = "SELECT CONCAT (Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'RPH' FROM Pharmacists JOIN Prescriptions ON Pharmacists.rph_id = Prescriptions.rph_id WHERE Pharmacists.rph_id = (SELECT rph_id FROM Prescriptions WHERE rx_number = %s);"
        cur = mysql.connection.cursor()
        cur.execute(rph_query, (rx_number,))
        rph = cur.fetchall()

        pharmacist_query="SELECT rph_id, CONCAT (rph_first_name, ' ', rph_last_name) AS 'RPH' FROM Pharmacists Order BY rph_first_name;"
        cur = mysql.connection.cursor()
        cur.execute(pharmacist_query)
        rph_data= cur.fetchall()
        
        return render_template("edit_prescriptions.j2", rx_data=rx_data, rph=rph, rph_data=rph_data)

    if request.method=="POST":
        if request.form.get("edit_rx"):            
            rx_date = request.form["date"]
            rph_id = request.form["rph_id"]
            units_dispensed = request.form["rx_quantity"]
            rx_price = request.form["price"]

            query = "UPDATE Prescriptions SET rx_date= %s, rph_id= %s, units_dispensed = %s, rx_price = %s WHERE rx_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(query, (rx_date, rph_id, units_dispensed, rx_price, rx_number,))
            mysql.connection.commit()

            drug_ndc_query = "SELECT drug_ndc FROM Prescriptions WHERE rx_number = %s;"
            cur = mysql.connection.cursor()
            cur.execute(drug_ndc_query, (rx_number,))
            drug_ndc = cur.fetchall()

            update_ndc = drug_ndc[0]["drug_ndc"]

            old_quantity = request.form["old_dispensed"]

            update_query= "UPDATE Drugs SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE Drugs.drug_ndc = %s) + %s - %s) WHERE Drugs.drug_ndc= %s;"
            cur = mysql.connection.cursor()
            cur.execute(update_query, (update_ndc, old_quantity, units_dispensed, update_ndc,))
            mysql.connection.commit()

            return redirect('/prescriptions')

# Listener
# change the port number if deploying on the flip servers
if __name__ == "__main__":
    app.run(port=17350, debug=True)
