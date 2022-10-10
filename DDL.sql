SET FOREIGN_KEY_CHECKS = 0;
SET AUTOCOMMIT = 0;

CREATE OR REPLACE TABLE Pharmacists
(
    rph_id INT NOT NULL AUTO_INCREMENT,
    rph_first_name VARCHAR(45) NOT NULL,
    rph_last_name VARCHAR(45) NOT NULL,
	ytd_rxs_processed INT NOT NULL DEFAULT 0,

    PRIMARY KEY (rph_id)
);

CREATE OR REPLACE TABLE Drugs
(	
	drug_ndc BIGINT UNIQUE NOT NULL,
	drug_name VARCHAR(45) NOT NULL,
	strength_in_mg INT not NULL,
    form VARCHAR(25) NOT NULL,
	is_generic TINYINT(1) DEFAULT 1 NOT NULL,
	manufacturer VARCHAR(25) NOT NULL,
	units_in_stock INT NOT NULL DEFAULT 0,
	
    PRIMARY KEY (drug_ndc)
);

CREATE OR REPLACE TABLE Prescriptions
(
    rx_number INT NOT NULL AUTO_INCREMENT,
    rph_id INT,
	rx_date DATETIME NOT NULL,
    drug_ndc BIGINT NOT NULL,
    units_dispensed INT NOT NULL,
    rx_price decimal(8,2) NOT NULL,
    
    PRIMARY KEY (rx_number),
    FOREIGN KEY (rph_id) REFERENCES Pharmacists(rph_id) ON DELETE SET NULL,
    FOREIGN KEY (drug_ndc) REFERENCES Drugs(drug_ndc) ON DELETE CASCADE
);

CREATE OR REPLACE TABLE Distributors (
    distributor_number INT NOT NULL UNIQUE AUTO_INCREMENT,
    distributor_name VARCHAR(45) NOT NULL,
    ytd_order_expenses DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (distributor_number)
);

CREATE OR REPLACE TABLE Invoices (
    po_number INT NOT NULL UNIQUE AUTO_INCREMENT,
    distributor_number INT,
    order_date DATE NOT NULL,
    order_cost DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (po_number),
    FOREIGN KEY (distributor_number) REFERENCES Distributors(distributor_number) ON DELETE SET NULL
);

CREATE OR REPLACE TABLE Drugs_Has_Invoices (
    drug_ndc BIGINT NOT NULL,
    po_number INT NOT NULL,
    units_ordered INT NOT NULL,
    drug_subtotal DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (drug_ndc, po_number),
    FOREIGN KEY (drug_ndc) REFERENCES Drugs(drug_ndc) ON DELETE CASCADE,
    FOREIGN KEY (po_number) REFERENCES Invoices(po_number) ON DELETE CASCADE
);

INSERT INTO Pharmacists (rph_first_name, rph_last_name) VALUES
('Mark', 'Chee'),
('Sora', 'Kim'),
('Brian', 'Lu'),
('Long', 'Phan'),
('Yueshi', 'Lin');

INSERT INTO Distributors (distributor_name) (
VALUES
('McKesson'),
('AmerisourceBergen'),
('Cardinal')
);

INSERT INTO Drugs (drug_ndc, drug_name, strength_in_mg, form, is_generic, manufacturer) VALUES
(54092038701, 'Adderall XR', 20, 'capsules', 0, 'Shire'),
(00406889201, 'Amphetamine Salts', 10, 'tablets', 1, 'Mallingkrodt'),
(00228306001, 'Amphetamine Salts ER', 20, 'capsules', 1, 'Actavis'),
(16714082201, 'Methylphenidate', 10, 'tablets', 1, 'Northstar'),
(59417010410, 'Vyvanse', 40, 'capsules', 0, 'Shire');

INSERT INTO Invoices (distributor_number, order_date) (
VALUES
(3, 20220301),
(2, 20220311),
(1, 20220321),
(1, 20220331)
);

INSERT INTO Drugs_Has_Invoices (drug_ndc, po_number, units_ordered, drug_subtotal) (
VALUES
(54092038701, 1, 1000, 314.15),
(00406889201, 2, 1000, 421.32),
(00228306001, 2, 1000, 185.45),
(16714082201, 2, 1000, 319.76),
(59417010410, 3, 333, 196.59),
(59417010410, 4, 667, 393.20)
);

UPDATE Invoices
SET order_cost = (SELECT SUM(drug_subtotal) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.po_number = 1) 
WHERE Invoices.po_number = 1;
UPDATE Invoices
SET order_cost = (SELECT SUM(drug_subtotal) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.po_number = 2) 
WHERE Invoices.po_number = 2;
UPDATE Invoices
SET order_cost = (SELECT SUM(drug_subtotal) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.po_number = 3) 
WHERE Invoices.po_number = 3;
UPDATE Invoices
SET order_cost = (SELECT SUM(drug_subtotal) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.po_number = 4) 
WHERE Invoices.po_number = 4;

UPDATE Distributors
SET ytd_order_expenses = (SELECT SUM(order_cost) FROM Invoices WHERE Invoices.distributor_number = 1)
WHERE Distributors.distributor_number = 1;
UPDATE Distributors
SET ytd_order_expenses = (SELECT SUM(order_cost) FROM Invoices WHERE Invoices.distributor_number = 2)
WHERE Distributors.distributor_number = 2;
UPDATE Distributors
SET ytd_order_expenses = (SELECT SUM(order_cost) FROM Invoices WHERE Invoices.distributor_number = 3)
WHERE Distributors.distributor_number = 3;

INSERT INTO Prescriptions (rph_id, rx_date, drug_ndc, units_dispensed, rx_price) VALUES
(1, 20220401, 54092038701, 30, 10.00),
(1, 20220402, 00406889201, 60, 5.47),
(4, 20220403, 59417010410, 30, 30.00),
(5, 20220403, 16714082201, 28, 4.25),
(3, 20220403, 00228306001, 14, 2.37);

UPDATE Drugs
SET units_in_stock = (SELECT SUM(units_ordered) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.drug_ndc = 54092038701) -
(SELECT SUM(units_dispensed) FROM Prescriptions WHERE Prescriptions.drug_ndc = 54092038701)
WHERE Drugs.drug_ndc = 54092038701;
UPDATE Drugs
SET units_in_stock = (SELECT SUM(units_ordered) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.drug_ndc = 00406889201) -
(SELECT SUM(units_dispensed) FROM Prescriptions WHERE Prescriptions.drug_ndc = 00406889201)
WHERE Drugs.drug_ndc = 00406889201;
UPDATE Drugs
SET units_in_stock = (SELECT SUM(units_ordered) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.drug_ndc = 00228306001) -
(SELECT SUM(units_dispensed) FROM Prescriptions WHERE Prescriptions.drug_ndc = 00228306001)
WHERE Drugs.drug_ndc = 00228306001;
UPDATE Drugs
SET units_in_stock = (SELECT SUM(units_ordered) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.drug_ndc = 16714082201) -
(SELECT SUM(units_dispensed) FROM Prescriptions WHERE Prescriptions.drug_ndc = 16714082201)
WHERE Drugs.drug_ndc = 16714082201;
UPDATE Drugs
SET units_in_stock = (SELECT SUM(units_ordered) FROM Drugs_Has_Invoices WHERE Drugs_Has_Invoices.drug_ndc = 59417010410) -
(SELECT SUM(units_dispensed) FROM Prescriptions WHERE Prescriptions.drug_ndc = 59417010410)
WHERE Drugs.drug_ndc= 59417010410;

UPDATE Pharmacists
SET ytd_rxs_processed = (SELECT COUNT(*) FROM Prescriptions WHERE Prescriptions.rph_id = 1 AND YEAR(rx_date) = YEAR(CURDATE()))
WHERE Pharmacists.rph_id=1;
UPDATE Pharmacists
SET ytd_rxs_processed = (SELECT COUNT(*) FROM Prescriptions WHERE Prescriptions.rph_id = 2 AND YEAR(rx_date) = YEAR(CURDATE()))
WHERE Pharmacists.rph_id=2;
UPDATE Pharmacists
SET ytd_rxs_processed = (SELECT COUNT(*) FROM Prescriptions WHERE Prescriptions.rph_id = 3 AND YEAR(rx_date) = YEAR(CURDATE()))
WHERE Pharmacists.rph_id=3;
UPDATE Pharmacists
SET ytd_rxs_processed = (SELECT COUNT(*) FROM Prescriptions WHERE Prescriptions.rph_id = 4 AND YEAR(rx_date) = YEAR(CURDATE()))
WHERE Pharmacists.rph_id=4;
UPDATE Pharmacists
SET ytd_rxs_processed = (SELECT COUNT(*) FROM Prescriptions WHERE Prescriptions.rph_id = 5 AND YEAR(rx_date) = YEAR(CURDATE()))
WHERE Pharmacists.rph_id=5;

SET FOREIGN_KEY_CHECKS = 1;
COMMIT;
