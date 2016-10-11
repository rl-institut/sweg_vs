###    Source code for SWEG (Simulation of wind energy based electricity generation)    ####

Author: Marcus Biank

Developed between June 2013 and March 2014

The code conforms to the Python 2.7 environment and most PEP rules

Explanation of the individual files:

sweg_vs_starter_full_configurability -- Startskript, das ein dictionary mit allen konfigurierbaren Simulationsparametern enthält. 
sweg_vs_starter_reduced_configurability -- Startskript, das ein dictionary mit ausgewählten konfigurierbaren Simulationsparametern enthält, der Rest wird über default Werte ergänzt. 
sweg_vs_main

/Modules/sweg_vs_additional_modules -- Modulsammlung mit allgemein nützlichen Funktionen für Datenkonvertierung, Datenbankzugriff, Dateizugriff, graphische Ausgabe
/Modules/sweg_vs_initialization -- SWEG Kernmodule 1
/Modules/sweg_vs_retrieve_db_data -- SWEG Kernmodule 2
/Modules/sweg_vs_retrieve_weatherdata -- SWEG Kernmodule 3
/Modules/sweg_vs_calculate_electricity_generation -- SWEG Kernmodule 4
/Modules/sweg_vs_calculate_cumulative_results -- SWEG Kernmodule 5
/Modules/sweg_vs_save_result2db -- SWEG Kernmodule 6

Weitere Infos finden sich in der dazugehörigen Master Thesis im Ordner ../../Thesis/Pdf/

Die abschließende Version vom 26.03.2014 wurde in einem git repository unter dem Namen "Version Masterarbeit Marcus Biank 2014-03-26" archiviert.


