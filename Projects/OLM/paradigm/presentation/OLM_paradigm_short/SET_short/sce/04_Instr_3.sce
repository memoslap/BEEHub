scenario = "block_1";     																								  
default_background_color = 255, 255, 255;
active_buttons = 2;
button_codes = 1,2;  																	 #1 Pfeil nach links=richtig,2 Pfeil nach rechts =falsch; 3= Leertaste ; 4-6= Tastatur 1,2,3
target_button_codes = 1,2;
#write_codes = true;
response_matching = simple_matching;
event_code_delimiter = ",";
#pulse_width = 10;

# fMRT
scenario_type = fMRI_emulation;
scan_period = 4500;

begin;  

 bitmap {filename = "instr_31.jpg";  width = 1280;height = 720; }instr_31;
 bitmap {filename = "instr_32.jpg";  width = 1280;height = 720; }instr_32;
 bitmap {filename = "instr_33.jpg";  width = 1280;height = 720; }instr_33;
 bitmap {filename = "instr_34.jpg";  width = 1280;height = 720; }instr_34;


# Intro1
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_31;
		 x=0; y=-0;  
	};
   code = "Anw1";   
}Instruc1;   

# Intro2
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_32;
		 x=0; y=-0; 
	};
   code = "Anw2";   
}Instruc2;

# Intro3
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_33;
		 x=0; y=-0;  
	};
   code = "Anw3";   
}Instruc3;

# Intro4
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 2;
	picture {
		bitmap instr_34;
		 x=0; y=-0; 
	};
   code = "Anw4";   
}Instruc4; 


begin_pcl;

Instruc1.present();
Instruc2.present();
Instruc3.present();
Instruc4.present();