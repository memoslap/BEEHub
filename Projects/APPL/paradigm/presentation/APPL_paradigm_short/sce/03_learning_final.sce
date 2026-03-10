scenario = "fMRI-SET-1";     																								  
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
bitmap { filename = ""; width = 600; height = 398; preload = false; } infoPic;
text { system_memory = true; font_color = 255, 255, 255; transparent_color = 0,0,0;	font_size = 100;caption = "...";} presWord;

################### STIMULUS TRIAL ###################################
trial {
	#trial_type = first_response;
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

trial {
	stimulus_event {
      picture { 
         bitmap infoPic; #picture
			x = 0; y = 0; 
         };
			time = 0;
		}InfoEvent;
}InfoTrial;

begin_pcl;

int pulse = 2;

array<string> hlcb[4] = {"bubbles/hello.jpg",
								"bubbles/learning.jpg",
								"bubbles/control.jpg",
								"bubbles/bye.jpg"};

array<string> LEARNINGpics1[5] = {"learning/PICTURE_513.jpg",
											"learning/PICTURE_24.jpg",
											"learning/PICTURE_40.jpg",
											"learning/PICTURE_245.jpg",
											"learning/PICTURE_397.jpg"};
LEARNINGpics1.shuffle();
											
array<string> LEARNINGpics2[5] = {"learning/PICTURE_673.jpg",
											"learning/PICTURE_354.jpg",
											"learning/PICTURE_606.jpg",
											"learning/PICTURE_308.jpg",
											"learning/PICTURE_321.jpg"};
LEARNINGpics2.shuffle();

array<string> LEARNINGwords1[5][5] = {{"Seltus","Geward","Gluktant","Mekter","Belschir"},
											{"Basut","Gluktant","Goser","Belschir","Mekte"},
											{"Priebem","Goser","Pafau","Mekte","Spiene"},
											{"Enelt","Pafau","Aume","Spiene","Petonsk"},
											{"Pofein","Aume","Geward","Petonsk","Mekter"}};
LEARNINGwords1.shuffle();
											
array<string> LEARNINGwords2[5][5] = {{"Ingal","Veschegt","Sporkel","Mummbant","Vewerm"},
											{"Aglud","Sporkel","Plumpent","Vewerm","Tompamm"},
											{"Lokrast","Plumpent","Volkant","Tompamm","Nazehl"},
											{"Ingam","Volkant","Straugel","Nazehl","Pakel"},
											{"Mobe","Straugel","Veschegt","Pakel","Mummbant"}};
LEARNINGwords1.shuffle();

array<string> LEARNING[10][6];
loop int i=1 until i>5
begin
	LEARNING[i][1] = LEARNINGpics1[i];
	LEARNING[i][2] = LEARNINGwords1[i][1];
	LEARNING[i][3] = LEARNINGwords1[i][2];
	LEARNING[i][4] = LEARNINGwords1[i][3];
	LEARNING[i][5] = LEARNINGwords1[i][4];
	LEARNING[i][6] = LEARNINGwords1[i][5];
	
	LEARNING[i+5][1] = LEARNINGpics2[i];
	LEARNING[i+5][2] = LEARNINGwords2[i][1];
	LEARNING[i+5][3] = LEARNINGwords2[i][2];
	LEARNING[i+5][4] = LEARNINGwords2[i][3];
	LEARNING[i+5][5] = LEARNINGwords2[i][4];
	LEARNING[i+5][6] = LEARNINGwords2[i][5];
		
	i = i + 1;
	
end;

#CHECK!!!!
loop int i=1 until i>LEARNING.count()
begin
	term.print_line(LEARNING[i][1] + " - " + LEARNING[i][2] + " - " + LEARNING[i][3] + " - " + LEARNING[i][4] + " - " + LEARNING[i][5] + " - " + LEARNING[i][6]);
	i = i + 1;
end;


# Load Trials
# 1 Learning Trials
# allPics[Picture, corrW, incorrW1, incorrW2, incorrW3, incorrW4] 
#array<string> LEARNING[30][6] = {{"learning/PICTURE_559.jpg","hiser","Leniel","Aschdel","Aglud","Letim"},
#											{"learning/PICTURE_640.jpg","geiten","Aschdel","Asir","Letim","Debal"},
#											{"learning/PICTURE_379.jpg","Flofe","Asir","Delgons","Debal","Libtrum"},
#											{"learning/PICTURE_465.jpg","geward","Delgons","Blastaun","Libtrum","Liegast"},
#											{"learning/PICTURE_592.jpg","mummbant","Blastaun","Leniel","Liegast","Aglud"},
#											{"learning/PICTURE_26.jpg","flister","Bogast","Letmap","Limjepp","Limmant"},
#   										{"learning/PICTURE_212.jpg","gluktant","Letmap","Deflas","Limmant","Lispad"},
#   										{"learning/PICTURE_38.jpg","helte","Deflas","Basut","Lispad","Logatt"},
#											{"learning/PICTURE_654.jpg","hürtem","Basut","Derbstal","Logatt","Logas"},
#											{"learning/PICTURE_659.jpg","schiehel","Derbstal","Bogast","Logas","Limjepp"},
#											{"learning/PICTURE_67.jpg","eume","Merschink","Dobast","Lokrast","Nazehl"},
#											{"learning/PICTURE_68.jpg","habel","Dobast","Dobul","Nazehl","Luttes"},
#											{"learning/PICTURE_71.jpg","enkor","Dobul","Fastrum","Luttes","Meidost"},
#											{"learning/PICTURE_72.jpg","bleine","Fastrum","Eidet","Meidost","Melant"},
#											{"learning/PICTURE_74.jpg","goser","Eidet","Merschink","Melant","Lokrast"},
#					   					{"learning/PICTURE_77.jpg","pase","Fastei","Duckel","Dieges","Fedit"},
#											{"learning/PICTURE_267.jpg","wonge","Duckel","Misal","Fedit","Molan"},
#											{"learning/PICTURE_97.jpg","dartin","Misal","Nakif","Molan","Najom"},
#											{"learning/PICTURE_100.jpg","tipnen","Nakif","Ferlas","Najom","Ferdat"},
#											{"learning/PICTURE_32.jpg","tummhaft","Ferlas","Fastei","Ferdat","Dieges"},
#											{"learning/PICTURE_148.jpg","pase","Nergunt","Flehsen","Lumack","Neffit"},
#											{"learning/PICTURE_156.jpg","sporkel","Flehsen","Negasch","Neffit","Flutoll"},
#											{"learning/PICTURE_165.jpg","stinnreik","Negasch","Fohreng","Flutoll","Nehal"},
#											{"learning/PICTURE_358.jpg","sprünte","Fohreng","Froltan","Nehal","Saptot"},
#											{"learning/PICTURE_202.jpg","larbe","Froltan","Nergunt","Saptot","Lumack"},
#											{"learning/PICTURE_203.jpg","wumze","Fugas","Gnatosch","Figat","Nerkanf"},
#											{"learning/PICTURE_224.jpg","furmi","Gnatosch","Harkun","Nerkanf","Jaloss"},
#											{"learning/PICTURE_566.jpg","lomig","Harkun","Heutil","Jaloss","Ningkal"},
#											{"learning/PICTURE_414.jpg","zabem","Heutil","Igat","Ningkal","Pafau"},
#											{"learning/PICTURE_245.jpg","mobe","Igat","Fugas","Pafau","Figat"}};


array<string> CONTROL[10][4] =  {{"control/PICTURE_156.jpg","Flöte","Besen","Mantel"},
											{"control/PICTURE_590.jpg","Besen","Mantel","Baby"},
											{"control/PICTURE_644.jpg","Mantel","Baby","Bogen"},
											{"control/PICTURE_674.jpg","Baby","Bogen","Flöte"},
											{"control/PICTURE_680.jpg","Bogen","Flöte","Besen"},
											{"control/PICTURE_559.jpg","Gurke","Kabel","Robbe"},
											{"control/PICTURE_523.jpg","Kabel","Robbe","Wespe"},
											{"control/PICTURE_92.jpg","Robbe","Wespe","Kiwi"},
											{"control/PICTURE_62.jpg","Wespe","Kiwi","Gurke"},
											{"control/PICTURE_125.jpg","Kiwi","Gurke","Kabel"}};

# [Trial, LS]
array<string> blk1[10][4];
array<string> blk2[10][4];
#array<string> blk3[10][4];
#array<string> blk4[10][4];
#array<string> blk5[10][4];
#array<string> blk6[10][4];

array<string> ctrl1[10][4];
array<string> ctrl2[10][4];

int a = 1;
int b = 1;
int c = 1;
int d = 1;
int e = 1;
int f = 1;


# dict. with all correct pairs
array<string> allCorrPairs[10][2];

#int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Marcus/A/Stimuli",  allPics );

##### extra Function please no Questions

sub string getRightName(string pic)
begin
	loop int i = 1 until i > 10
	begin
		if pic == allCorrPairs[i][1] then
			
			return allCorrPairs[i][2];
		end;
	i = i + 1;
	end;

	return "-1";
	
end;

#Make Blocks

loop int i = 1 until i > LEARNING.count()
	begin
		if (i<=5) then	# Block 1
			# learning 1
			blk1[a][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";		   #correct [pic,presWORD, corrWORD]
			blk1[a+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";		#incorrect [pic,presWORD, corrWORD]
			# learning 2
			blk1[a][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk1[a][3]  = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk1[a][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			a = a + 2;
		elseif(i>5) && (i<=10) then	# Block 2
			# learning 1
			blk2[b][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk2[b][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk2[b][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk2[b][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			b = b + 2;
		
		end;
		i = i+1;
	end;

a = 1;
b = 1;

CONTROL.shuffle();
loop int i = 1 until i > CONTROL.count() 
begin
	#if i<=10 then
		# learning 1
		ctrl1[a][1] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl1[a+1][1] = CONTROL[i][1] + ";" + CONTROL[i][3] + ";" + CONTROL[i][2] + ";i";
		# learning 2
		ctrl1[a][2] = CONTROL[i][1] + ";" + CONTROL[i][2]+ ";" + CONTROL[i][2] + ";c";
		ctrl1[a+1][2] = CONTROL[i][1] + ";" + CONTROL[i][4] + ";" + CONTROL[i][2] + ";i";
		# learning 3
		ctrl1[a][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl1[a+1][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][3] + ";" + CONTROL[i+1][2] + ";i";
		# learning 4
		ctrl1[a][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl1[a+1][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][4] + ";" + CONTROL[i+1][2] + ";i";
		a = a + 2;
		
	#else
		# learning 1
#		ctrl2[b][1] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
#		ctrl2[b+1][1] = CONTROL[i][1] + ";" + CONTROL[i][3] + ";" + CONTROL[i][2] + ";i";
#		# learning 2
#		ctrl2[b][2] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
#		ctrl2[b+1][2] = CONTROL[i][1] + ";" + CONTROL[i][4] + ";" + CONTROL[i][2] + ";i";
#		# learning 3
#		ctrl2[b][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2]+ ";" + CONTROL[i+1][2] + ";c";
#		ctrl2[b+1][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][3] + ";" + CONTROL[i+1][2] + ";i";
#		# learning 4
#		ctrl2[b][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
#		ctrl2[b+1][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][4] + ";" + CONTROL[i+1][2] + ";i";
#		b = b + 2;
		
	#end;
	i = i + 2;
end;

# Check Trial Train. 
array<int> BlockOrder[] = {1,2,3}; ## 3 = Contro 

array<string> Task_List[3][4][10];

loop int blk = 1 until blk > 3
begin
	loop int ls = 1 until ls > 4
	begin
		loop int item = 1 until item > 10
		begin
			# Blocks
			if blk == 1 then
				Task_List[blk][ls][item] = blk1[item][ls];
			elseif blk == 2 then
				Task_List[blk][ls][item] = blk2[item][ls];
			elseif blk == 3 then
				Task_List[blk][ls][item] = ctrl1[item][ls];
			end;
			item = item + 1;
		end;
		
		## Shuffle lStage Items
		array<string> dummy[10];
		bool isOK = false;
		loop until isOK
		begin
			dummy = Task_List[blk][ls];
			dummy.shuffle();
			Task_List[blk][ls] = dummy;
			loop int k = 1 until k > 9
			begin
				#term.print_line(k);
				#term.print_line(LSpairs[block][lStage][k]);
				#term.print_line(LSpairs[block][lStage][k+1]);
				array<string> N[1];
				array<string> N2[1];
				Task_List[blk][ls][k].split(";",N);
				Task_List[blk][ls][k+1].split(";",N2);	
			
				if N[1] == N2[1] || N[2] == N2[2] || N[3] == N2 [2] then
					#term.print_line("NÖÖÖ");
					isOK = false;
					break;
					
				else
					isOK = true;	
				end;	
			k = k + 1;
			end;
			
		end;
		
		ls = ls + 1;	
		
	end;
	
	blk = blk + 1;
end;



################## write corr Pair-list #######
#string id = logfile.subject();
#id = id + "_corrPair.txt";
#output_file ofile = new output_file;

#ofile.open(id, true); #overwrite true
#int n = 1;
#loop int b = 1 until b > 4
#begin 
#	loop int w=1 until w > 10
#	begin
#	ofile.print(corrWords[b][w] + ";" + corrPics[b][w] + "\n");
#	allCorrPairs[n][1] = corrPics[b][w];
#	allCorrPairs[n][2] = corrWords[b][w];
#	n = n + 1; 
#	w = w + 1;
#end;
#b = b + 1;
#end;
#ofile.close();
###############################################			

# make random order of LEARNING- and CONTROL-Blocks
int isOrderOK = 0;
loop until isOrderOK == 1
begin
	BlockOrder.shuffle();
	isOrderOK = 1;
	loop int x = 2 until x > BlockOrder.count()
	begin
		if BlockOrder[1] == 3 || BlockOrder[3] == 3 then
			isOrderOK = 0;
			break;	
		end;
		x = x +1 ;
	end;
end;
#check
loop int i = 1 until i > BlockOrder.count()
begin
	
	term.print_line(BlockOrder[i]);
	i = i + 1;
end;

##### INTRO
string introText = "Das Experiment\nbeginnt gleich.\nSind Sie bereit?";

FeedText.set_caption(introText, true);
FeedEvent.set_event_code("Hello - Intro");
FeedTrial.set_duration(100);
#FeedTrial.set_type(first_response);
FeedTrial.present();

bool firstTrial = true;
#Block 1 to 4
loop int blk = 1 until blk > 3
begin
	int currBlk = BlockOrder[blk];
	##############################
	#term.print_line("#####");
	#loop int i = 1 until i > allPairs.count()
	#begin
	#	term.print_line(allPairs[i]);
	#	i = i + 1;
	#end;
	#term.print_line("#####");
	##############################
	
	# Block-Intro
	###############
	string infoBubble = "";
	bool exit = false;
	if currBlk == 3 then
		infoBubble = hlcb[3];	# Control
	elseif  blk == 3 then
		infoBubble = hlcb[4];	# bye
		exit = true;
	else
		infoBubble = hlcb[2];	# learning
	end;
	
	#Start with Scanner-Pulse synchr.
	if firstTrial then
		fixTrial.set_mri_pulse(pulse);
		firstTrial = false;
	end;
	
	if !exit then
		## Fix 4 pulses between blocks
		loop f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(infoBubble);
				infoPic.set_draw_mode(1);
				InfoEvent.set_event_code(infoBubble);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;
	
	
	
	
	loop int ls = 1 until ls > 4
	begin
		loop int i = 1 until i > 10
		begin
			
			int oldRespCount = response_manager.total_response_count();
			
			array<string> strParts[1];
			Task_List[currBlk][ls][i].split(";",strParts);	
			presPic.set_filename(strParts[1]); 														# set bitmap filename
			presWord.set_caption(strParts[2]);
			stimEvent.set_duration(2500);		
			stimEvent.set_event_code(Task_List[currBlk][ls][i] + ";block"+string(blk)+ ";LS"+ string(ls));
							
			presPic.set_draw_mode(1);
			presPic.load();
			presWord.redraw();
			presWord.load();
			
			##Start with Scanner-Pulse synchr.
			#if firstTrial then
			#	StimTrial.set_mri_pulse(pulse);
			#	firstTrial = false;
			#end;			
			
			StimTrial.present();
			
			# Create Feedback depending on Response
			stimulus_data lastStim = stimulus_manager.last_stimulus_data();
			response_data lastResp = response_manager.last_response_data();
			
			#term.print_line(lastStim.time());
			#term.print_line(lastResp.code());
			#term.print_line(lastResp.time());
			#term.print_line("########");
			FeedTrial.set_duration(2000);
			
			#### need to catch only the first response!
			int CurrRespCount = response_manager.total_response_count();
			int targetResp = oldRespCount + 1;
			term.print_line(string(targetResp));
			if targetResp < CurrRespCount then	
				lastResp = response_manager.get_response_data( targetResp );
			else
				lastResp = response_manager.last_response_data();
			end;
			
			
			
			# Need to catch for the first trial, if there is no response
			int respCount = response_manager.response_count();
			int resTime = 0;
			#term.print_line(string(respCount));
			if respCount == 0 then
				resTime = lastStim.time()+3000;
			else
				resTime = lastResp.time();
			end;
						
			# Too late or not
			if resTime >lastStim.time() && resTime <= (lastStim.time() + 2500) then
				
				if (strParts[4] == "c"  && lastResp.code() == 1) || (strParts[4] == "i"  && lastResp.code() == 2) then
					FeedText.set_caption("Korrekt, das ist " + strParts[3], true);
					FeedEvent.set_event_code("Korrekt, das ist " + strParts[3]);
					FeedTrial.present();
				else
					# all other
					FeedText.set_caption("Falsch, das ist " + strParts[3], true);
					FeedEvent.set_event_code("Falsch, das ist " + strParts[3]);
					FeedTrial.present();
				end;
							
			else
				
				FeedText.set_caption("Zu spät, das ist " + strParts[3], true);
				FeedEvent.set_event_code("Zu spät, das ist " + strParts[3]);
				FeedTrial.present();
				
			end;
					
		
			pulse = pulse + 1;
								
			i = i+1;
				
		end;
		## Fix between learning stage
		#fixTrial.set_mri_pulse(pulse);
		fixTrial.set_duration(4500);	
		fixTrial.present();
		pulse = pulse + 1;
		ls = ls + 1;
	end;
	
	if exit then
		## Fix 4 pulses between blocks
		loop f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(infoBubble);
				infoPic.set_draw_mode(1);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;			
	
	
blk = blk + 1;
end;









