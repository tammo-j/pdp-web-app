The installation instructions for the PDP ticket printer
--------------------------------------------------------

1.	Take a standard Raspberry Pi using Raspbian and login to console.

2.	Upgrade the Raspbian system packages to latest versions
		sudo apt-get update
		sudo apt-get upgrade

3.	Install additional required system packages for printing
		sudo apt-get install cups libcups2-dev libcupsimage2-dev python-cups python-imaging

4.	Install and compile the Dymo LabelWriter drivers
		wget http://download.dymo.com/Software/Linux/dymo-cups-drivers-1.4.0.tar.gz
		tar zxvf dymo-cups-drivers-1.4.0.tar.gz
		cd dymo-cups-drivers-1.4.0.5/
		./configure
		make
		sudo make install
		cd

5.	Connect and power up the Dymo LabelWriter

6.	Add a user you are going to use to the printer admin group, here user is `pi`
		sudo adduser pi lpadmin

7. 	Add printer via CUPS web interface
	> To enter X (GUI) run `startx`. Start web browser e.g. `midori`.
	> By default CUPS allows access only from the localhost. If there is no monitor one
	> option is to install a text based browser like `links2`. 
	1.	Go to `http://localhost:631` and select `Administration`
	2.	Select `Add printer` and login with the shell user from step 6
	3.	Select `Dymo LabelWriter` in `Local Printer` and `Continue`
	4.	Keep default names and `Continue`
	5.	Keep the detected model (drivers) and `Add Printer`

8.	Configure printer using the CUPS web interface
	1.	Select `Printers`
	2.	Select `Dymo_LabelWriter_4xx`
	3.	Under `Administration` select `Set As Server Default`
	4.	Under `Administration` select `Set Default Options`
	5.	Select `Media Size` by the code in the label box you are using and `Set Default Options`
	6.	Under `Maintenance` select `Print Test Page` and see you get one label printed
	7.	Close browser and logout from X (GUI) 

10.	Install uwsgi application server and the print_ticket Python application
		sudo apt-get install uwsgi uwsgi-plugin-python
		wget http://debyte.fi/tmp/shn/print_ticket.tar.gz
		tar zxvf print_ticket.tar.gz

11. Run the print server
		sudo uwsgi --plugin python,http --http :80 --wsgi-file print_ticket.py

