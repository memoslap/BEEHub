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

 bitmap {filename = "instr_11.jpg";  width = 1280;height = 720; }instr_11;
 bitmap {filename = "instr_12.jpg";  width = 1280;height = 720; }instr_12;
 bitmap {filename = "instr_13.jpg";  width = 1280;height = 720; }instr_13;
 bitmap {filename = "instr_14.jpg";  width = 1280;height = 720; }instr_14;
 bitmap {filename = "instr_15.jpg";  width = 1280;height = 720; }instr_15;
 bitmap {filename = "instr_16.jpg";  width = 1280;height = 720; }instr_16;
 bitmap {filename = "instr_17.jpg";  width = 1280;height = 720; }instr_17;

# Intro1
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_11;
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
		bitmap instr_12;
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
		bitmap instr_13;
		 x=0; y=-0;  
	};
   code = "Anw3";   
}Instruc3;

# Intro4
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_14;
		 x=0; y=-0; 
	};
   code = "Anw4";   
}Instruc4; 

# Intro5
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_15;
		 x=0; y=-0;  
	};
   code = "Anw5";   
}Instruc5; 

# Intro6
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1;
	picture {
		bitmap instr_16;
		 x=0; y=-0; 
	};
   code = "Anw6";   
}Instruc6; 

# Intro7
trial { 
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 2;
	picture {
		bitmap instr_17;
		 x=0; y=-0; 
	};
   code = "Anw7";   
}Instruc7; 


begin_pcl;

Instruc1.present();
Instruc2.present();
Instruc3.present();
Instruc4.present();
Instruc5.present();
Instruc6.present();
Instruc7.present();
