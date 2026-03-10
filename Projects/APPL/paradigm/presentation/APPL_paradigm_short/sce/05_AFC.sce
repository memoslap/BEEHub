scenario = "block_1";     																								  
default_background_color = 0, 0, 0;
active_buttons = 3;
button_codes = 1,2,3;  																	 # Tastatur 1,2,3
target_button_codes = 1,2,3;
response_matching = simple_matching;
event_code_delimiter = ",";

# fMRT
#scenario_type = fMRI_emulation;
#scan_period = 4500;


begin;


bitmap { filename = ""; width = 1324; height = 1087; preload = false; } presPic;


#main trial

trial {
	trial_duration = forever; 
   trial_type = specific_response;
   terminator_button = 1,2,3;
	stimulus_event {
      picture { 
			#  picture
         bitmap presPic; 
			x = 0; y = 0; 
         } picStim; 
			time = 0;
		}stimEvent1;
#	stimulus_event {
#		picture { 
#			text {
#			system_memory = true;
#			font_color = 255, 255, 255;
#			font_size = 100;
#			caption = "-";
#		} respText;
#		x = 0; y = 0;
#		
#		}picStim2;
#		time = 2500;
#		}stimEvent2;

}mainTrial;

begin_pcl;

array<string> afcPics[1];

string picP = "C:/Users/malinowskir/Desktop/Locato40_2ver/Version_A/Stimuli/AFC";

int picNum = get_directory_files(picP,  afcPics); 

afcPics.shuffle();

loop int i = 1 until i >picNum
			begin
				if (afcPics[i].find(".jpg") != 0)	then 		
					array<string> strParts[1];
					afcPics[i].split("\\",strParts);
					stimEvent1.set_event_code(strParts[strParts.count()]);
					presPic.set_filename(afcPics[i]); 			
					presPic.set_draw_mode(1);
					presPic.load();
					mainTrial.present();
			
				end;
			
				i = i+1;
				
				end;
				
				
				
				
				
				
				
				
				
				