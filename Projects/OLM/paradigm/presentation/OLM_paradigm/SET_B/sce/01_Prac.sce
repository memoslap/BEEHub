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
bitmap { filename = ""; width = 1024; height = 787; preload = false; } presPicFB;


#main trial
###########
trial {
	stimulus_event {
      picture { 
			#  picture
         bitmap presPic; 
			x = 0; y = -70; 
         } picStim; 
			time = 0;
		}stimEvent1;
	#stimulus_event {
	#	picture { 
	#		text {
	#		system_memory = true;
	#		font_color = 255, 255, 255;
	#		font_size = 100;
	#		caption = "-";
	#	} respText;
	#	x = 0; y = 0;
	#	
	#	}picStim2;
	#	time = 2500;
	#	}stimEvent2;

}mainTrial;
##### FeedBack - Trial #######
trial {
	
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 70;
			caption = "-";
		} FeedText;
		x = 0; y = 400;
		bitmap presPicFB; 
		x = 0; y = -70; 
		
		}FeedPic1;
		time = 0;
		}FeedEvent1;
		

}FeedTrial;
###########
#trial {
#	stimulus_event {
#     picture { 
#			#  picture
#         bitmap presPic; 
#			x = 0; y = 0; 
#         } picStim; 
#			time = 0;
#		}stimEvent1;
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
#
#}mainTrial;


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

array<string> picPairs[10][2];

sub array<string,2> getAllPic(string picP)
begin
	array<string> picPairs2[10][2];
	array<string> allFiles[1];
	
	int k = 1;
	
	int picNum = get_directory_files(picP,  allFiles ); 			

	loop int i = 1 until i > picNum
		begin
			if (allFiles[i].find(".jpg") != 0)	then 							
				#term.print_line(allFiles[i]);
				array<string> strParts[1];
				allFiles[i].split("\\",strParts);
			
				if (strParts[strParts.count()].find("k") != 0)	then
					picPairs2[k][1] = allFiles[i];
					array<string> strParts2[1];
					strParts[strParts.count()].split("p",strParts2);
										
					#term.print_line(picPairs2[k][1]);
					#term.print_line(picPairs2.count());
					k = k+1;
				end;
			end;
			i = i + 1;
		end;
		

		loop int i = 1 until i > picPairs2.count()
			begin
				array<string> strParts[1];
				picPairs2[i][1].split("\\",strParts);
				array<string> strParts2[1];
				strParts[strParts.count()].split("p",strParts2);
				int x = 2;
				loop int j = 1 until j > picNum
					begin
						array<string> strParts3[1];
						allFiles[j].split("\\",strParts3);
						if (strParts3[strParts3.count()].find(strParts2[1]+"p") != 0	&& strParts3[strParts3.count()].find("i") != 0) then
							picPairs2[i][x] = allFiles[j];
							x = 3
						end;
						j = j+1;
					end;
				
				i = i +1;
			end;
			
			#check
			loop int i = 1 until i > picPairs2.count()
				begin
					term.print_line(picPairs2[i][1]);
					term.print_line(picPairs2[i][2]);
					
					i = i +1;
				end;
			
			
		
	return picPairs2;
end;

picPairs = getAllPic("C:/Users/malinowskir/Desktop/Agnes/Locato40_AB_ver2/Version_A/Stimuli/prac");


term.print_line(picPairs.count());

array<string> one_Ten[20][2];
int one = 1;
loop int i = 1 until i > picPairs.count()
		begin
			if (i<=10) then
				# learning 1
				one_Ten[one][1] = picPairs[i][1] ;
				one_Ten[one+1][1] = picPairs[i][2] ;
				# learning 2
				one_Ten[one][2] = picPairs[i][1] ;
				one_Ten[one+1][2] = picPairs[i][2] ;
				one = one + 2;
			end;
			i = i+1;
		end;
		





#int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Locato40_2ver/Version_A/Stimuli/prac",  one_Ten ); 	
###########
#Block1
loop int l = 1 until l > 2
	begin
	one_Ten.shuffle();
	loop int i = 1 until i > one_Ten.count()
			begin
				term.print_line(one_Ten[i][1]);
				term.print_line(one_Ten[i][2]);			
				presPic.set_filename(one_Ten[i][l]); 														# set bitmap filename
				
				array<string> strParts[1];
				one_Ten[i][l].split("\\",strParts);
						
				stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
				presPic.set_draw_mode(1);
				presPic.load();
			
				mainTrial.set_mri_pulse(pulse);
				mainTrial.set_duration(2500);
				mainTrial.present();
				
				# Feedback
				# Create Feedback depending on Response
				stimulus_data lastStim = stimulus_manager.last_stimulus_data();
				response_data lastResp = response_manager.last_response_data();
				FeedTrial.set_duration(2000);
				## load the right Pic
				
				term.print_line(one_Ten[i][1]);
				term.print_line(one_Ten[i][2]);
				#term.print_line(one_Ten[i][3]);
				#term.print_line(one_Ten[i][l]);
				#term.print("##");
				#term.print_line(picPairs[1][1]);
				#term.print_line(picPairs[1][2]);
				#term.print_line(picPairs[1][3]);
				
				string corrFBpic;
											
				loop int k = 1 until k > picPairs.count()
				begin
					if picPairs[k][2] == one_Ten[i][l]  then	#|| picPairs[k][3] == one_Ten[i][l]
						corrFBpic = picPairs[k][1];
						break;
					else
						corrFBpic = one_Ten[i][l];
					end;
					k = k + 1;
				end;
				
				array<string> strParts2[1];
				corrFBpic.split("\\",strParts2);

				presPicFB.set_filename(corrFBpic);
				presPicFB.set_draw_mode(1);
				presPicFB.load();
				
				if lastResp.time() >lastStim.time() && lastResp.time() <= (lastStim.time() + 2500) then
					
					if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("i") != 0) && lastResp.code() == 2) then
						FeedText.set_caption("Antwort richtig, die korrekte Position ist:", true);
						
						FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
						FeedTrial.present();
					else
						FeedText.set_caption("Antwort falsch, die korrekte Position ist:", true);
						#stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
						FeedEvent1.set_event_code("incorrect;" + strParts2[strParts2.count()]);
												
						FeedTrial.present();
					end;
					
				else
			
					FeedText.set_caption("Zu spät, die korrekte Position ist:", true);
					FeedEvent1.set_event_code("to late");
					FeedTrial.present();
			
				end;
				
				pulse = pulse +1;
			
				i = i+1;
			
		end;
		
		fixTrial.set_mri_pulse(pulse);
		fixTrial.present();
		pulse = pulse +1;
	
	l = l + 1;
	end;
###########







#Block1  2x reicht evtl.
#loop int l = 1 until l > 2
#	begin
#	one_Ten.shuffle();
#	loop int i = 1 until i > one_Ten.count()
#			begin
#							
#				presPic.set_filename(one_Ten[i]); 														# set bitmap filename
#				
#				array<string> strParts[1];
#				one_Ten[i].split("\\",strParts);
#						
#				if (strParts[strParts.count()].find("k") != 0) then
#					respText.set_caption("Richtige Position", true);
#					stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
#					stimEvent2.set_event_code("Richtige Position");
#				else
#					respText.set_caption("Falsche Position", true);
#					stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
#					stimEvent2.set_event_code("Falsche Position");
#				end;
#				presPic.set_draw_mode(1);
#				presPic.load();
#			
#				mainTrial.set_mri_pulse(pulse);
#				mainTrial.present();
#			
#				pulse = pulse +1;
#			
#				i = i+1;
#			
#		end;
#		
#		fixTrial.set_mri_pulse(pulse);
#		fixTrial.present();
#		pulse = pulse +1;
#	
#	l = l+1;
#	end;



	














