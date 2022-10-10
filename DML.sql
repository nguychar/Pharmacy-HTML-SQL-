-- Entity/Implementation
-- Drugs: CRU
-- Pharmacists: CRUD
-- Prescriptions: CRUD
-- Invoices: CRUD
-- Drugs_Has_Invoices: CRUD
-- Distributors: CRUD

-- Inventory Main Page (index.html)
-- This page lists all of the drugs in the inventory.
-- It allows the user to add a new drug to the inventory or create a new prescription.

-- Query to display all Drugs in inventory.
SELECT
drug_ndc AS 'NDC',
CONCAT(drug_name, ' ', strength_in_mg, ' ', form) AS 'Drug',
manufacturer AS 'Manufacturer',
units_in_stock AS 'Quantity'
FROM Drugs
ORDER BY drug_name;

-- Query to create new Drug.
INSERT INTO Drugs (drug_ndc, drug_name, strength_in_mg, form, manufacturer, is_generic)
VALUES
(%s, %s, %s, %s, %s, %s);

-- Query to display all Pharmacists available for selecting to fill a new Prescription.
SELECT
rph_id,
CONCAT (rph_first_name, ' ', rph_last_name) AS 'RPH'
FROM Pharmacists
Order BY rph_first_name;

-- Query to create new Prescription.
INSERT INTO Prescriptions (drug_ndc, rx_date, rph_id, units_dispensed, rx_price)
VALUES
(%s, %s, %s, %s, %s);

-- Query to update units in stock based upon new Prescription.
UPDATE Drugs
SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s)
WHERE Drugs.drug_ndc= %s;

-- Drug Audit Page (drug_audit.html)
-- This page allows for updating a specific Drug and checking the Invoice/Prescription history of a specific Drug.

-- Query to show single Drug information.
SELECT
* FROM Drugs
WHERE drug_ndc = %s;

-- Query to update single Drug information.
UPDATE Drugs
SET form = %s, manufacturer = %s
WHERE drug_ndc = %s;

-- Query to show all Prescriptions for a given Drug.
SELECT
Prescriptions.rx_date AS 'Date Dispensed',
Prescriptions.rx_number AS 'Prescription Number',
Prescriptions.units_dispensed AS 'Quantity Dispensed',
CONCAT(Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'Rph'
FROM Prescriptions
LEFT JOIN Pharmacists ON Pharmacists.rph_id = Prescriptions.rph_id
WHERE Prescriptions.drug_ndc = %s
ORDER BY Prescriptions.rx_date;

-- Query to show all Invoice records for a given Drug.
SELECT
Invoices.order_date AS 'Invoice Date',
Invoices.po_number AS 'PO Number',
Distributors.distributor_name AS 'Distributor',
Drugs_Has_Invoices.units_ordered AS 'Quantity Ordered'
FROM Invoices
LEFT JOIN Drugs_Has_Invoices ON Invoices.po_number = Drugs_Has_Invoices.po_number AND Drugs_Has_Invoices.drug_ndc = %s
JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number
WHERE Drugs_Has_Invoices.drug_ndc = %s;

-- Pharmacists Page (pharmacists.html)
-- This page displays all of the current Pharmacists.
-- It allows for the addition, removal, or updating of a given Pharmacist.

-- Query to display all Pharmacists.
SELECT
Pharmacists.rph_id,
Pharmacists.rph_first_name AS 'First Name',
Pharmacists.rph_last_name AS 'Last Name',
COUNT(Prescriptions.rph_id) AS '# of C2s Processed'
FROM Pharmacists
LEFT JOIN Prescriptions ON Pharmacists.rph_id = Prescriptions.rph_id
GROUP BY Pharmacists.rph_id;

-- Query to select a specific Pharmacist to update.
SELECT
*
FROM Pharmacists
WHERE rph_id = %s;

-- Query to update a given Pharmacist.
UPDATE Pharmacists
SET rph_first_name = %s, rph_last_name = %s
WHERE rph_id = %s;

-- Query to create a new Pharmacist.
INSERT INTO Pharmacists (rph_first_name, rph_last_name)
VALUES
(%s, %s);

-- Query to remove a Pharmacist.
DELETE
FROM Pharmacists
WHERE rph_id = %s;

-- Prescriptions Page (prescriptions.html)
-- This page displays all of the Prescriptions sorted by date.
-- It allows for updating or deleting Prescriptions.

-- Query to display all Prescriptions.
SELECT
rx_number,
rx_date AS 'Date',
CONCAT(drug_name, ' ', strength_in_mg) AS 'Drug Dispensed',
units_dispensed AS 'Quantity',
CONCAT(Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'RPH'
FROM Prescriptions JOIN Drugs ON Drugs.drug_ndc = Prescriptions.drug_ndc
LEFT JOIN Pharmacists ON Prescriptions.rph_id = Pharmacists.rph_id
ORDER BY Prescriptions.rx_date DESC;

-- Query to select a Prescription to be updated.
SELECT
*
FROM Prescriptions
WHERE rx_number = %s;

-- Query to select the Pharmacist associated with the Prescription to be updated.
SELECT
CONCAT (Pharmacists.rph_first_name, ' ', Pharmacists.rph_last_name) AS 'RPH'
FROM Pharmacists
JOIN Prescriptions ON Pharmacists.rph_id = Prescriptions.rph_id
WHERE Pharmacists.rph_id = (SELECT rph_id FROM Prescriptions WHERE rx_number = %s);

-- Query to select the Pharmacists who may be associated with the Prescription to be updated.
SELECT
rph_id,
CONCAT (rph_first_name, ' ', rph_last_name) AS 'RPH'
FROM Pharmacists
Order BY rph_first_name;

-- Query to update a Prescription.
UPDATE Prescriptions
SET rx_date= %s, rph_id= %s, units_dispensed = %s, rx_price = %s
WHERE rx_number = %s;

-- Query to select the Drug associated with the updated Prescription.
SELECT
drug_ndc
FROM Prescriptions
WHERE rx_number = %s;

-- Query to update the units_in_stock attribute of Drugs upon updating a Prescription.
UPDATE Drugs
SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE Drugs.drug_ndc = %s) + %s - %s)
WHERE Drugs.drug_ndc= %s;

-- Query to select the information associated with a Drug for a Prescription to be deleted.
SELECT
drug_ndc,
units_dispensed
FROM Prescriptions
WHERE rx_number = %s;

-- Query to delete a Prescription.
DELETE
FROM Prescriptions
WHERE rx_number = %s;

-- Query to update the units_in_stock attribute of Drugs to account for a deleted Prescription.
UPDATE Drugs
SET units_in_stock = ((SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s)
WHERE drug_ndc = %s;

-- Invoices Page (invoices.html)
-- This page displays all of the Invoices sorted by date.
-- It allows the user to create, edit, or delete an Invoice.

-- Query to display all Invoices.
SELECT
Invoices.po_number,
Distributors.distributor_name AS 'Distributor',
Invoices.order_date AS 'Order Date',
IFNULL(SUM(Drugs_Has_Invoices.drug_subtotal), 0) AS 'Order Cost ($)'
FROM Invoices
JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number
LEFT JOIN Drugs_Has_Invoices ON Drugs_Has_Invoices.po_number = Invoices.po_number
GROUP BY Invoices.po_number
ORDER BY Invoices.order_date DESC;

-- Query to select all Distributors.
SELECT
*
FROM Distributors;

-- Query to add an Invoice.
INSERT INTO Invoices (distributor_number, order_date)
VALUES
((SELECT distributor_number FROM Distributors WHERE distributor_name = %s), %s);

-- Query to select the information of a single Invoice for updating.
SELECT
Invoices.po_number,
Distributors.distributor_name AS 'Distributor',
Invoices.order_date AS 'Order Date',
IFNULL(SUM(Drugs_Has_Invoices.drug_subtotal), 0) AS 'Order Cost ($)'
FROM Invoices
JOIN Distributors ON Distributors.distributor_number = Invoices.distributor_number
LEFT JOIN Drugs_Has_Invoices ON Drugs_Has_Invoices.po_number = Invoices.po_number
WHERE Invoices.po_number = %s;

-- Query to update an Invoice.
UPDATE Invoices
SET distributor_number = (SELECT distributor_number FROM Distributors WHERE distributor_name = %s), order_date = %s, order_cost = %s
WHERE po_number = %s;

-- Query to select all associated Drugs_Has_Invoices transactions of an Invoice.
SELECT
*
FROM Drugs_Has_Invoices
WHERE po_number = %s;

-- Query to update units_in_stock attribute of Drugs based upon transactions of a deleted Invoice.
UPDATE Drugs
SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s
WHERE drug_ndc = %s;

-- Query to delete an Invoice.
DELETE
FROM Invoices
WHERE po_number = '%s';

-- Drugs_Has_Invoices Page (transaction.html)
-- This page displays the individual transactions of a given Invoice, as well as all of the transactions across all Invoices.
-- It allows the user to add, edit, or delete a transaction for the currently selected Invoice.

-- Query to display the information of the current Invoice.
SELECT
*
FROM Invoices
WHERE po_number = %s;

-- Query to display current Invoice Drugs_Has_Invoices transactions.
SELECT
*
FROM Drugs_Has_Invoices
WHERE po_number = %s;

-- Query to add a Drugs_Has_Invoices transaction to a given Invoice.
INSERT INTO Drugs_Has_Invoices (drug_ndc, po_number, units_ordered, drug_subtotal)
VALUES
(%s, %s, %s, %s);

-- Query to update the order_cost attribute of Invoices based upon the added transaction.
UPDATE Invoices
SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) + %s
WHERE po_number = %s;

-- Query to select the Distributor of the current transaction.
SELECT
distributor_name
FROM Distributors
WHERE distributor_number = %s;

-- Query to select all Drugs available for selecting for a transaction.
SELECT
CONCAT (drug_ndc, ' (', drug_name, ')') AS DRUG
FROM Drugs;

-- Query to update Drug units_in_stock accordingly after adding a transaction.
UPDATE Drugs
SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s
WHERE drug_ndc = %s;

-- Query to edit a Drugs_Has_Invoices transaction.
UPDATE Drugs_Has_Invoices
SET units_ordered = %s, drug_subtotal = %s
WHERE drug_ndc = %s AND po_number = %s;

-- Query to update order_cost attribute of Invoices for the updated transaction.
UPDATE Invoices
SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) + %s - %s
WHERE po_number = %s;

-- Query to update units_in_stock attribute of Drugs for the updated transaction.
UPDATE Drugs
SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) + %s - %s
WHERE drug_ndc = %s;

-- Query to select the information of a single transaction about to be updated or deleted.
SELECT
*
FROM Drugs_Has_Invoices
WHERE po_number = %s and drug_ndc = %s;

-- Query to delete a Drugs_Has_Invoices transaction.
DELETE
FROM Drugs_Has_Invoices
WHERE po_number = %s AND drug_ndc = %s;

-- Query to update the order_cost attribute of Invoices based upon the deleted transaction. 
UPDATE Invoices
SET order_cost = (SELECT order_cost FROM Invoices WHERE po_number = %s) - %s
WHERE po_number = %s;

-- Query to update units_in_stock attribute of Drugs for the deleted transaction.
UPDATE Drugs
SET units_in_stock = (SELECT units_in_stock FROM Drugs WHERE drug_ndc = %s) - %s
WHERE drug_ndc = %s;

-- Distributors Page (distributors.html)
-- This page displays all of the Distributors and their associated expenses.
-- It allows for the addition, updating, or deletion of new Distributors.

-- Query to add a Distributor.
INSERT INTO Distributors (distributor_name)
VALUES
(%s);

-- Query to display all Distributors.
SELECT
Distributors.distributor_number AS 'Number',
Distributors.distributor_name AS 'Distributor Name',
IFNULL(SUM(Invoices.order_cost), 0) AS 'Total Expenses'
FROM Distributors
LEFT JOIN Invoices ON Distributors.distributor_number = Invoices.distributor_number
GROUP BY Distributors.distributor_number;

-- Query to display a single Distributor for updating.
SELECT
Distributors.distributor_number,
Distributors.distributor_name,
IFNULL(SUM(Invoices.order_cost), 0)
FROM Distributors
LEFT JOIN Invoices ON Distributors.distributor_number = Invoices.distributor_number
WHERE Distributors.distributor_number = %s;

-- Query to update a Distributor.
UPDATE Distributors
SET distributor_name = %s
WHERE distributor_number = %s;

-- Query to delete a Distributor.
DELETE
FROM Distributors
WHERE distributor_number = '%s';
