scenario = "block_1";     																								  
default_background_color = 0, 0, 0;
active_buttons = 2;
button_codes = 1,2;  	#1 Pfeil nach links=richtig,2 Pfeil nach rechts =falsch; 3= Leertaste ; 4-6= Tastatur 1,2,3
target_button_codes = 1,2;
#write_codes = true;
response_matching = simple_matching;
event_code_delimiter = ",";
#pulse_width = 10;

# fMRT
scenario_type = fMRI_emulation;
scan_period = 4500;



begin;


bitmap { filename = ""; width = 600; height = 600; preload = false; } presPic;
text { system_memory = true; font_color = 255, 255, 255; transparent_color = 0,0,0;	font_size = 100;caption = "...";} presWord;

################### STIMULUS TRIAL ###################################
trial {
	stimulus_event {
      picture { 
         bitmap presPic; #picture
			x = 0; y = 0; 
         text presWord; 
			x = 0; y = -400; 
         } picStim;
			time = 0;
		}stimEvent;
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

}StimTrial;

################### FEEDBACK TRIAL ###################################
trial {
	
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 100;
			caption = "-";
		} FeedText;
		x = 0; y = 0;
		}feedPic;
		time = 0;
		}FeedEvent;

}FeedTrial;


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

array<string> corrWords[4][10] = {{"Ahep", "Beme", "Dila", "Efes", "Filt", "Gulm", "Kage", "Nolo", "Ripa", "Silk"}, 
											{"Bans", "Dede", "Gahe", "Jila", "Maku", "Palu", "Pihe", "Seho", "Unam", "Zebi"},
											{"Bini", "Digu", "Ilso", "Lasu", "Nalf", "Pird", "Rahi", "Tade", "Ured", "Zuba"},
											{"Bulb", "Enik", "Flar", "Golb", "Inwa", "Kurn", "Lasa", "Nunk", "Olor", "Romp"}};
array<string> corrPics[4][10];

array<string> incorrPics[4][2][10];

array<string> allPics[1];

array<string> aPClear[40];

# dict. with all correct pairs
array<string> allCorrPairs[40][2];

int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Marcus/A/Stimuli",  allPics );

##### extra Function please no Questions

sub string getRightName(string pic)
begin
	loop int i = 1 until i > 40
	begin
		if pic == allCorrPairs[i][1] then
			
			return allCorrPairs[i][2];
		end;
	i = i + 1;
	end;

	return "-1";
	
end;

# del non *.png files
int jj = 1;
loop int i = 1 until i > picNum
	begin
		#term.print_line(allPics[i].find(".png"));
		int isPNG = allPics[i].find(".png");
		if isPNG > 0 then
			aPClear[jj] = allPics[i];
			#term.print_line(string(jj));	
			#term.print_line(aPClear[jj]);
			jj = jj + 1;
			
			i = i + 1;
		else
			i = i + 1;
		end;
		
	end;

allPics.resize(aPClear.count());
allPics = aPClear;
picNum = allPics.count();

#loop int i = 1 until i > picNum
#begin
#	term.print_line(allPics[i]);
#	i = i + 1;
#end;


# rand. pics
allPics.shuffle();

# make list of corr pairs
loop int i = 1 until i > picNum
begin
# Block 1
	if i<=10 then
		#10 cor pair
		corrPics[1][i] = allPics[i];
		#2 x 10 incorr
		int k1 = random(1, 40);
		int k2 = random(1, 40);
		loop until k1>10 && k2>10 && k1!=k2
		begin
			k1 = random(1, 40);
			k2 = random(1, 40);
		end;
		#term.print_line("Block1 i<=10: " + string(k1) + " and " + string(k2));
		incorrPics[1][1][i] = allPics[k1];
		incorrPics[1][2][i] = allPics[k2];
			
	# Block 2	
	elseif i>10 && i<=20 then
		corrPics[2][i-10] = allPics[i];
		#2 x 10 incorr
		int k1 = random(1, 40);
		int k2 = random(1, 40);
		loop until (k1<=10 && k2 <=10 && k1!=k2) || (k1<=10 && k2>20 && k1!=k2) ||(k1>20 && k2<=10 && k1!=k2) || (k1>20 && k2>20 && k1!=k2)
		begin
			k1 = random(1, 40);
			k2 = random(1, 40);
		end;
		#term.print_line("Block2 i>10 && i<=20: " + string(k1) + " and " + string(k2));
		incorrPics[2][1][i-10] = allPics[k1];
		incorrPics[2][2][i-10] = allPics[k2];
		# Block 3	
	elseif i>20 && i<=30 then
		corrPics[3][i-20] = allPics[i];
		#2 x 10 incorr
		int k1 = random(1, 40);
		int k2 = random(1, 40);
		loop until (k1<=20 && k2 <=20 && k1!=k2) || (k1<=20 && k2>30 && k1!=k2) ||(k1>30 && k2<=20 && k1!=k2) || (k1>30 && k2>30 && k1!=k2)
		begin
			k1 = random(1, 40);
			k2 = random(1, 40);
		end;#
		#term.print_line("Block3 i>20 && i<=30: " + string(k1) + " and " + string(k2));
		incorrPics[3][1][i-20] = allPics[k1];
		incorrPics[3][2][i-20] = allPics[k2];
		# Block 4	
	elseif i>30 && i<=40 then
		corrPics[4][i-30] = allPics[i];
		#2 x 10 incorr
		int k1 = random(1, 40);
		int k2 = random(1, 40);
		loop until k1<=30 && k2<=30 && k1!=k2
		begin
			k1 = random(1, 40);
			k2 = random(1, 40);
		end;
		#term.print_line("Block4 i>30 && i<=40: " + string(k1) + " and " + string(k2));
		incorrPics[4][1][i-30] = allPics[k1];
		incorrPics[4][2][i-30] = allPics[k2];
	end;
	i=i+1;
end;

################# write corr Pair-list #######
string id = logfile.subject();
id = id + "_corrPair.txt";
output_file ofile = new output_file;

ofile.open(id, true); #overwrite true
int n = 1;
loop int b = 1 until b > 4
begin 
	loop int w=1 until w > 10
	begin
	ofile.print(corrWords[b][w] + ";" + corrPics[b][w] + "\n");
	allCorrPairs[n][1] = corrPics[b][w];
	allCorrPairs[n][2] = corrWords[b][w];
	n = n + 1; 
	w = w + 1;
end;
b = b + 1;
end;
ofile.close();
###############################################			
#Block 1 to 4
loop int l = 1 until l > 4
begin
	
	# make the 80 trials
	bool initial = true;
	array<string> allPairs[1];
	array<string> learningStage[20];
	string rword;
	loop int k = 1 until k > 2
	begin
		int p = 1;
		loop int j = 1 until j>10
		begin
			
			rword = getRightName(corrPics[l][j]);
			learningStage[p] = corrWords[l][j] +";" + corrPics[l][j] + ";c" + ";" + rword;
			#term.print_line(learningStage[p]);
			p=p+1;
			rword = getRightName(incorrPics[l][1][j]);
			learningStage[p] = corrWords[l][j] +";" + incorrPics[l][1][j] + ";i" + ";" + rword;
			#term.print_line(learningStage[p]);
			p=p+1;
			
			
			j = j+1;	
		end;
		
		learningStage.shuffle();	
		
		if initial then
			allPairs.resize(learningStage.count());
			allPairs = learningStage;
			initial = false;
		else
			allPairs.append(learningStage);
		end;
		
			
		p = 1;
		loop int j = 1 until j>10
		begin
			rword = getRightName(corrPics[l][j]);
			learningStage[p] = corrWords[l][j] +";" + corrPics[l][j] + ";c" + ";" + rword;
			#term.print_line(learningStage[p]);
			p=p+1;
			rword = getRightName(incorrPics[l][2][j]);
			learningStage[p] = corrWords[l][j] +";" + incorrPics[l][2][j] + ";i" + ";" + rword;
			#term.print_line(learningStage[p]);
			p=p+1;
			
			j = j+1;			
		end;
		learningStage.shuffle();	
			
		if initial then
			allPairs.resize(learningStage.count());
			allPairs = learningStage;
			initial = false;
		else
			allPairs.append(learningStage);
		end;
		
	k = k + 1;
	end;
	
	##############################
	term.print_line("#####");
	loop int i = 1 until i > allPairs.count()
	begin
		term.print_line(allPairs[i]);
		i = i + 1;
	end;
	term.print_line("#####");
	##############################
	
	loop int i = 1 until i > allPairs.count()
	begin
		array<string> strParts[1];
		allPairs[i].split(";",strParts);	
		presPic.set_filename(strParts[2]); 														# set bitmap filename
		presWord.set_caption(strParts[1]);
		stimEvent.set_duration(2500);		
		stimEvent.set_event_code(  allPairs[i] + ";mri_pulse:" + string(pulse));
						
		presPic.set_draw_mode(1);
		presPic.load();
		presWord.redraw();
		presWord.load();
					
		StimTrial.set_mri_pulse(pulse);
		StimTrial.present();
		
		# Create Feedback depending on Response
		stimulus_data lastStim = stimulus_manager.last_stimulus_data();
		response_data lastResp = response_manager.last_response_data();
		
		term.print_line(lastStim.time());
		#term.print_line(lastResp.code());
		term.print_line(lastResp.time());
		term.print_line("########");
		
		# Too late or not
		if lastResp.time() >lastStim.time() && lastResp.time() <= (lastStim.time() + 2500) then
			
			if (strParts[3] == "c"  && lastResp.code() == 1) || (strParts[3] == "i"  && lastResp.code() == 2) then
				FeedText.set_caption("Korrekt, das ist " + strParts[4], true);
				FeedEvent.set_event_code("Korrekt, das ist " + strParts[4]);
				FeedTrial.present();
			else
				# all other
				FeedText.set_caption("Falsch, das ist " + strParts[4], true);
				FeedEvent.set_event_code("Falsch, das ist " + strParts[4]);
				FeedTrial.present();
			end;
						
		else
			
			FeedText.set_caption("Zu spät, das ist " + strParts[4], true);
			FeedEvent.set_event_code("Zu spät, das ist " + strParts[4]);
			FeedTrial.present();
			
		end;
				
	
		pulse = pulse + 1;
				
		if i == 20 || i == 40 || i == 60 then
			fixTrial.set_mri_pulse(pulse);
			fixTrial.present();
			pulse = pulse + 1;
		end;
				
		i = i+1;
			
	end;
		
		
	
	## Fix 4 pulses
	loop int f = 1 until f > 4
	begin
		fixTrial.set_mri_pulse(pulse);
		fixTrial.present();
		pulse = pulse +1;
		f = f +1;
	end;	
	
	
l = l + 1;
end;

## Fix 4 pulses
#loop int f = 1 until f > 4
#	begin
#		fixTrial.set_mri_pulse(pulse);
#		fixTrial.present();
#		pulse = pulse +1;
#		f = f +1;
#	end;	
	
	







