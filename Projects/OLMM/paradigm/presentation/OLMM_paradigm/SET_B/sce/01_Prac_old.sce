scenario = "block_1";     																								  
default_background_color = 0, 0, 0;
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


bitmap { filename = ""; width = 1024; height = 787; preload = false; } presPic;


trial {
	stimulus_event {
     picture { 
			#  picture
         bitmap presPic; 
			x = 0; y = 0; 
         } picStim; 
			time = 0;
		}stimEvent1;
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 100;
			caption = "-";
		} respText;
		x = 0; y = 0;
		
		}picStim2;
		time = 2500;
		}stimEvent2;

}mainTrial;


trial {
	picture { 
		text {
		system_memory = true;
		font_color = 255, 255, 255;
		font_size = 100;
		caption = "+";
		} fixText;
		x = 0; y = 0;	
		}fixStim;
		time = 0;
		code = "fix";
}fixTrial;

begin_pcl;

int pulse = 2;

array<string> one_Ten[20];

int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Agnes/Locato40_AB_ver2/Version_A/Stimuli/prac",  one_Ten ); 	

term.print_line(picNum);

#Block1  2x reicht evtl.
loop int l = 1 until l > 2
	begin
	one_Ten.shuffle();
	loop int i = 1 until i > one_Ten.count()
			begin
							
				presPic.set_filename(one_Ten[i]); 				# set bitmap filename
				
				array<string> strParts[1];
				one_Ten[i].split("\\",strParts);
						
				if (strParts[strParts.count()].find("k") != 0) then
					respText.set_caption("Richtige Position", true);
					stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
					stimEvent2.set_event_code("Richtige Position");
				else
					respText.set_caption("Falsche Position", true);
					stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
					stimEvent2.set_event_code("Falsche Position");
				end;
				presPic.set_draw_mode(1);
				presPic.load();
			
				mainTrial.set_mri_pulse(pulse);
				mainTrial.present();
			
				pulse = pulse +1;
			
				i = i+1;
			
		end;
		
		fixTrial.set_mri_pulse(pulse);
		fixTrial.present();
		pulse = pulse +1;
	
	l = l+1;
	end;



	














