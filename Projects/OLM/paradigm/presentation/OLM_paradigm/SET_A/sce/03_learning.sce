scenario = "block_1";     																								  
default_background_color = 0, 0, 0;
active_buttons = 2;
button_codes = 1,2;  		#1 Pfeil nach links=richtig,2 Pfeil nach rechts =falsch; 3= Leertaste ; 4-6= Tastatur 1,2,3
target_button_codes = 1,2;
#write_codes = true;
response_matching = simple_matching;
event_code_delimiter = ",";
#pulse_width = 10;

# fMRT
#scenario_type = fMRI_emulation;
#scan_period = 4500;

scenario_type = fMRI;
pulses_per_scan = 1;
scan_period = 1000;
pulse_code = 30;
pulse_width = 6; 

begin;


bitmap { filename = ""; width = 1024; height = 787; preload = false; } presPic;
bitmap { filename = ""; width = 600; height = 398; preload = false; } infoPic;
bitmap { filename = ""; width = 1024; height = 787; preload = false; } presPicFB;


#main trial

trial {
	stimulus_event {
      picture { 
			#  picture
         bitmap presPic; 
			x = 0; y = -70; 
         } picStim; 
			time = 0;
		}stimEvent1;

}mainTrial;
##### FeedBack - Trial #######
trial {
	
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 65;
			caption = "-";
		} FeedText;
		x = 0; y = 400;
		bitmap presPicFB; 
		x = 0; y = -70; 
		
		}FeedPic1;
		time = 0;
		}FeedEvent1;
		
}FeedTrial;

trial {
	
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 100;
			caption = "-";
		} IntroText;
		x = 0; y = 0;
		}IntroPic;
		time = 0;
		}IntroEvent;

}IntroTrial;

trial {
	stimulus_event {
      picture { 
         bitmap infoPic; #picture
			x = 0; y = 0; 
         };
			time = 0;
		}InfoEvent;
}InfoTrial;

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

int pulse = 4;
array<string> hlcb[3] = {"bubbles/learning.png",
								"bubbles/control.png",
								"bubbles/bye.png"};

# Change 30 -> 28
array<string> picPairsBLK1[7][4];
array<string> picPairsBLK2[7][4];
array<string> picPairsBLK3[7][4];
array<string> picPairsBLK4[7][4];
array<string> ctrPics1[1];
array<string> ctrPics2[1];



sub array<string,2> getAllPic(string picP)
begin
	array<string> picPairs2[7][4];
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
					k = k + 1;
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
						if (strParts3[strParts3.count()].find(strParts2[1]+"p") != 0	&& strParts3[strParts3.count()].find("_i_") != 0) then
							picPairs2[i][x] = allFiles[j];
							x = x + 1;
						end;
						j = j+1;
					end;
				
				i = i + 1;
			end;
			
			#check
			#loop int i = 1 until i > picPairs2.count()
			#	begin
			#		term.print_line(picPairs2[i][1]);
			#		term.print_line(picPairs2[i][2]);
			#		term.print_line(picPairs2[i][3]);
			#		term.print_line("##");
			#		i = i +1;
			#	end;
			
			
		
	return picPairs2;
end;

picPairsBLK1 = getAllPic("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/learning/block1");
picPairsBLK2 = getAllPic("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/learning/block2");
picPairsBLK3 = getAllPic("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/learning/block3");
picPairsBLK4 = getAllPic("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/learning/block4");

int picNum1 = get_directory_files("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/control/block1",  ctrPics1 ); 
int picNum2 = get_directory_files("C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_A/Stimuli/control/block2",  ctrPics2 ); 

#picPairs.shuffle();

# get all up´s and all down´s
#array<string> ups[14][3];
#array<string> downs[14][3];
#int u = 1;
#int d = 1;
#loop int i = 1 until i>picPairs.count()
#begin
#	array<string> strParts[1];
#	picPairs[i][1].split("\\",strParts);
#	string dummy = strParts[strParts.count()];
#	#term.print_line(dummy);
#	dummy.split("_",strParts);
#	
#	if strParts[4] == "up" then
#		ups[u] = picPairs[i];
#		u = u + 1;
#	elseif strParts[4] == "down" then
#		downs[d] = picPairs[i];
#		d = d + 1;
#	end;
#	i = i + 1; 
#end;
#############check
##loop int i = 1 until i>ups.count()
##begin
##	term.print_line(ups[i][1]);
##	i = i + 1;
##end;
##loop int i = 1 until i>downs.count()
##begin
##	term.print_line(downs[i][1]);
##	i = i + 1;
##end;
#
#int n = 1;
#loop int i = 1 until i > ups.count()
#begin
#	picPairs[n] = ups[i];
#	picPairs[n+1] = downs[i];
#	n = n + 2;
#	i = i + 1;
#end;
############check
#loop int i = 1 until i>picPairs.count()
#begin
#	term.print_line(picPairs[i][1]);
#	i = i + 1;
#end;	

############check
loop int i = 1 until i > picPairsBLK1.count()
	begin
		term.print_line(picPairsBLK1[i][1]);
		term.print_line(picPairsBLK1[i][2]);
		term.print_line(picPairsBLK1[i][3]);
		term.print_line(picPairsBLK1[i][4]);
		term.print_line("##");
		i = i +1;
	end;
	
#split into Blocks

array<string> blk1[14][4];
array<string> blk2[14][4];
array<string> blk3[14][4];
array<string> blk4[14][4];
#array<string> blk5[10][4];
#array<string> blk6[10][4];

array<string> ctrl1[14][4];
array<string> ctrl2[14][4];

int one = 1;
int two = 1;
int three = 1;
int four = 1;
int five = 1;
int six = 1;




int ctrl_one = 1;
int ctrl_two = 1;

array<int> random_numbers1[14] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14};
array<int> random_numbers2[14] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14};

random_numbers1.shuffle();
random_numbers2.shuffle();

loop int i = 1 until i > random_numbers1.count() 
begin
	#if i<=7 then
		# learning 1
		ctrl1[i][1] = ctrPics1[random_numbers1[i]];
		
		# learning 2
		ctrl1[i][2] = ctrPics1[random_numbers1[i]];
	
		# learning 3
		ctrl1[i][3] = ctrPics1[random_numbers1[i]];
	
		# learning 4
		ctrl1[i][4] = ctrPics1[random_numbers1[i]];
		
	
		
	#else
		# learning 1
		ctrl2[i][1] = ctrPics2[random_numbers2[i]];
		
		# learning 2
		ctrl2[i][2] = ctrPics2[random_numbers2[i]];
	
		# learning 3
		ctrl2[i][3] = ctrPics2[random_numbers2[i]];
		
		# learning 4
		ctrl2[i][4] = ctrPics2[random_numbers2[i]];
		
		
	#end;
	i = i + 1;
end;

#check
loop int i = 1 until i > 7
begin
	term.print_line(random_numbers1[i]);
	i = i + 1;
end;

#check
loop int i = 1 until i > 7
begin
	term.print_line(random_numbers2[i]);
	i = i + 1;
end;
loop int i = 1 until i > picPairsBLK1.count()
	begin
		#if (i<=7) then	# Block 1
			# learning 1
			blk1[one][1] = picPairsBLK1[i][1] ;
			blk1[one+1][1] = picPairsBLK1[i][2] ;
			# learning 2
			blk1[one][2] = picPairsBLK1[i][1] ;
			blk1[one+1][2] = picPairsBLK1[i][3] ;
			# learning 3
			blk1[one][3] = picPairsBLK1[i][1] ;
			blk1[one+1][3] = picPairsBLK1[i][4] ;
			# learning 4
			blk1[one][4] = picPairsBLK1[i][1] ;
			blk1[one+1][4] = picPairsBLK1[i][2] ;
			one = one + 2;
		#elseif(i>7) && (i<=14) then	# Block 2
			# learning 1
			blk2[two][1] = picPairsBLK2[i][1] ;
			blk2[two+1][1] = picPairsBLK2[i][3] ;
			# learning 2
			blk2[two][2] = picPairsBLK2[i][1] ;
			blk2[two+1][2] = picPairsBLK2[i][2] ;
			# learning 3
			blk2[two][3] = picPairsBLK2[i][1] ;
			blk2[two+1][3] = picPairsBLK2[i][3] ;
			# learning 4
			blk2[two][4] = picPairsBLK2[i][1] ;
			blk2[two+1][4] = picPairsBLK2[i][4] ;
			two = two + 2;
		#elseif(i>14) && (i<=21) then	# Block 3
			# learning 1
			blk3[three][1] = picPairsBLK3[i][1] ;
			blk3[three+1][1] = picPairsBLK3[i][4];
			# learning 2
			blk3[three][2] = picPairsBLK3[i][1] ;
			blk3[three+1][2] = picPairsBLK3[i][3];
			# learning 3
			blk3[three][3] = picPairsBLK3[i][1];
			blk3[three+1][3] = picPairsBLK3[i][2];
			# learning 4
			blk3[three][4] = picPairsBLK3[i][1];
			blk3[three+1][4] = picPairsBLK3[i][3];
			three = three + 2;	
		#elseif(i>21) && (i<=28) then	# Block 4
			# learning 1
			blk4[four][1] = picPairsBLK4[i][1] ;
			blk4[four+1][1] = picPairsBLK4[i][2];
			# learning 2
			blk4[four][2] = picPairsBLK4[i][1] ;
			blk4[four+1][2] = picPairsBLK4[i][3];
			# learning 3
			blk4[four][3] = picPairsBLK4[i][1] ;
			blk4[four+1][3] = picPairsBLK4[i][4];
			# learning 4
			blk4[four][4] = picPairsBLK4[i][1] ;
			blk4[four+1][4] = picPairsBLK4[i][2] ;
			four = four + 2;
		
		#end;
		i = i+1;
	end;

# make random order of LEARNING- and CONTROL-Blocks
array<string> order[] = {"learning-1","learning-2","learning-3","learning-4","control","control"};
int isOrderOK = 0;
loop until isOrderOK == 1
begin
	order.shuffle();
	isOrderOK = 1;
	loop int x = 2 until x > order.count()
	begin
		if order[1] == "control" || order[x-1] == order[x] then
			isOrderOK = 0;
			break;	
		end;
		x = x +1 ;
	end;
end;

array<string> ctrl12[] = {"1","2"};
ctrl12.shuffle();
int c = 1;

loop int i = 1 until i > order.count()
begin
	if order[i] == "control" then
		order[i] = "control-" + ctrl12[c];
		c = c + 1;
	end;
	
	i = i + 1;
end;

#check
loop int i = 1 until i > order.count()
begin
	term.print_line(order[i]);
	i = i + 1;
end;

### Shuffle items in LS


sub array<string,2> shuffleItems(array<string,2> in)
begin
	array<string> out[14][4];
	
	array<string> dummy[14];


	loop int Lstage = 1  until Lstage > 4
	begin
		
	###blk1
		bool isOK = false;
		loop until isOK
		begin
			
			term.print_line("####");
			loop int j = 1 until j > 14
			begin
				dummy[j] = in[j][Lstage];
				j = j +1;
			end;
			dummy.shuffle();
			loop int j = 1 until j > 14
			begin
				out[j][Lstage]  = dummy[j];
				j = j +1;
			end;
			
				
			loop int k = 1 until k > 13
			begin
				#N1
				array<string> dummy2[1];
				out[k][Lstage].split("\\",dummy2);
				array<string> dummy3[1];
				dummy2[dummy2.count()].split("_",dummy3);
				string N1 = dummy3[1];
				
				#N2
				dummy2[1];
				out[k+1][Lstage].split("\\",dummy2);
				dummy3[1];
				dummy2[dummy2.count()].split("_",dummy3);
				string N2 = dummy3[1];
				
				if N1 == N2 then
					#term.print_line("Nö");
					isOK = false;
					break;
					
				else
					isOK = true;	
				end;	
				
			term.print_line(N1+"-"+N2);
			k = k +1;
			end;		
									
		end;
	#########################################################

	Lstage = Lstage + 1;	
	end;
		
	return out;
	
end;


blk1 = shuffleItems(blk1);
blk2 = shuffleItems(blk2);
blk3 = shuffleItems(blk3);
blk4 = shuffleItems(blk4);


int blockIndex = 1;
int ctrIndex = 1;		
bool firstTrial = true;

##### INTRO
string itrText = "Das Experiment\nbeginnt gleich.\n\n Zu Erinnerung: \n   Ja = Zeigefinger\n Nein = Daumen";

IntroText.set_caption(itrText, true);
IntroEvent.set_event_code("Hello - Intro");
IntroTrial.set_duration(100);
#FeedTrial.set_type(first_response);
IntroTrial.present();

### For Controltesting:

#order = {"control-1","control-2","control-1","control-2","control-1","control-2","control-1","control-2"};

loop int masterIndex = 1 until masterIndex > order.count()
begin
	
		# Block-Intro
	###############
	string infoBubble = "";
	bool exit = false;
	
	if masterIndex == 8 then
		exit = true;
		if order[masterIndex] == "control-1" || order[masterIndex] == "control-2"  then
			infoBubble = hlcb[2];	# Control
		else
			infoBubble = hlcb[1];	# learning
		end;
	else
		if order[masterIndex] == "control-1" || order[masterIndex] == "control-2"  then
			infoBubble = hlcb[2];	# Control
		else
			infoBubble = hlcb[1];	# learning
		end;
	end;
	if firstTrial then
		fixTrial.set_mri_pulse(pulse);
		firstTrial = false;
	end;
	
	loop int f = 1 until f > 4
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
		
	
	if order[masterIndex] == "learning-1" then

		#Block1
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			#blk1.shuffle();
			loop int i = 1 until i > blk1.count()
					begin
									
						presPic.set_filename(blk1[i][l]); 														# set bitmap filename
						
						array<string> strParts[1];
						blk1[i][l].split("\\",strParts);
								
						stimEvent1.set_event_code(  strParts[strParts.count()] + ";block"+string(blockIndex)+ ";LS"+ string(l));
						
						presPic.set_draw_mode(1);
						presPic.load();
						
						if firstTrial then
							mainTrial.set_mri_pulse(pulse);
							firstTrial = false;
						end;
						
						mainTrial.set_duration(2500);
						mainTrial.set_type(first_response);
						mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						
						# Need to catch for the first trial, if there is no response
						int respCount = response_manager.response_count();
						int resTime = 0;
						#term.print_line(string(respCount));
						if respCount == 0 then
							resTime = lastStim.time()+3000;
						else
							resTime = lastResp.time();
						end;
						
						
						FeedTrial.set_duration(2000);
						## load the right Pic
						
						#term.print_line(one_Ten[i][1]);
						#term.print_line(one_Ten[i][2]);
						#term.print_line(one_Ten[i][3]);
						#term.print_line(one_Ten[i][l]);
						#term.print("##");
						#term.print_line(picPairs[1][1]);
						#term.print_line(picPairs[1][2]);
						#term.print_line(picPairs[1][3]);
						
						
						string corrFBpic;
													
						loop int k = 1 until k > picPairsBLK1.count()
						begin
							if picPairsBLK1[k][2] == blk1[i][l] || picPairsBLK1[k][3] == blk1[i][l] || picPairsBLK1[k][4] == blk1[i][l] then
								corrFBpic = picPairsBLK1[k][1];
								break;
							else
								corrFBpic = blk1[i][l];
							end;
							k = k + 1;
						end;
						
						array<string> strParts2[1];
						corrFBpic.split("\\",strParts2);

						presPicFB.set_filename(corrFBpic);
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						
						
						if resTime >lastStim.time() && resTime <= (lastStim.time() + 2500) then
							
							int deltaTime = 2500 - (resTime - lastStim.time()); # toGo
							stimEvent1.set_event_code("extra Pic Time");
							mainTrial.set_duration(deltaTime);
							mainTrial.set_type(fixed);
							
							mainTrial.present();
							
							
							if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("_i_") != 0) && lastResp.code() == 2) then

								FeedText.set_caption("Richtig, die korrekte Position ist:", true);
								
								FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
								FeedTrial.present();
							else
								FeedText.set_caption("Falsch, die korrekte Position ist:", true);
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
				
				#fixTrial.set_mri_pulse(pulse);
				fixTrial.set_duration(4500);
				fixTrial.present();
				pulse = pulse +1;
			
			l = l + 1;
			end;
		blockIndex = blockIndex + 1;
		# Fix 4 pulses
		#loop int f = 1 until f > 4
		#	begin
		#		#fixTrial.set_mri_pulse(pulse);
		#		fixTrial.set_duration(4500);
		#		fixTrial.present();
		#		pulse = pulse +1;
		#		f = f +1;
		#	end;	
		######################################################################	
		
	elseif order[masterIndex] == "learning-2" then
		#Block2
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			#blk2.shuffle();
			loop int i = 1 until i > blk2.count()
					begin
						
						presPic.set_filename(blk2[i][l]); 														# set bitmap filename
						
						array<string> strParts[1];
						blk2[i][l].split("\\",strParts);
								
						stimEvent1.set_event_code(  strParts[strParts.count()] + ";block"+string(blockIndex)+ ";LS"+ string(l));
						
						presPic.set_draw_mode(1);
						presPic.load();
					
						if firstTrial then
							mainTrial.set_mri_pulse(pulse);
							firstTrial = false;
						end;
						mainTrial.set_duration(2500);
						mainTrial.set_type(first_response);
						mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						
						
						FeedTrial.set_duration(2000);
						# Need to catch for the first trial, if there is no response
						int respCount = response_manager.response_count();
						int resTime = 0;
						#term.print_line(string(respCount));
						if respCount == 0 then
							resTime = lastStim.time()+3000;
						else
							resTime = lastResp.time();
						end;
						
						## load the right Pic
						
						string corrFBpic;
													
						loop int k = 1 until k > picPairsBLK2.count()
						begin
							if picPairsBLK2[k][2] == blk2[i][l] || picPairsBLK2[k][3] == blk2[i][l] || picPairsBLK2[k][4] == blk2[i][l] then
								corrFBpic = picPairsBLK2[k][1];
								break;
							else
								corrFBpic = blk2[i][l];
							end;
							k = k + 1;
						end;
						
						array<string> strParts2[1];
						corrFBpic.split("\\",strParts2);

						presPicFB.set_filename(corrFBpic);
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						
						if resTime > lastStim.time() && resTime <= (lastStim.time() + 2500) then
							
							int deltaTime = 2500 - (resTime - lastStim.time()); # toGo
							stimEvent1.set_event_code("extra Pic Time");
							mainTrial.set_duration(deltaTime);
							mainTrial.set_type(fixed);
							
							mainTrial.present();
							
							
							if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("_i_") != 0) && lastResp.code() == 2) then
								FeedText.set_caption("Richtig, die korrekte Position ist:", true);
								
								FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
								FeedTrial.present();
							else
								FeedText.set_caption("Falsch, die korrekte Position ist:", true);
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
				
					#fixTrial.set_mri_pulse(pulse);
					fixTrial.set_duration(4500);
					fixTrial.present();
					pulse = pulse +1;
				
				l = l + 1;	

			end;
		blockIndex = blockIndex + 1;
		# Fix 4 pulses
		#loop int f = 1 until f > 4
		#	begin
		#		#fixTrial.set_mri_pulse(pulse);
		##		fixTrial.set_duration(4500);
			#	fixTrial.present();
		#		pulse = pulse +1;
		#		f = f+1;
		#	end;	
		######################################################################
		
	elseif order[masterIndex] == "learning-3" then
	
		#Block3
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			#blk3.shuffle();
			loop int i = 1 until i > blk3.count()
					begin
						
						presPic.set_filename(blk3[i][l]); 														# set bitmap filename
						
						array<string> strParts[1];
						blk3[i][l].split("\\",strParts);
								
						stimEvent1.set_event_code(  strParts[strParts.count()] + ";block"+string(blockIndex)+ ";LS"+ string(l));
						
						presPic.set_draw_mode(1);
						presPic.load();
					
						if firstTrial then
							mainTrial.set_mri_pulse(pulse);
							firstTrial = false;
						end;
						mainTrial.set_duration(2500);
						mainTrial.set_type(first_response);
						mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						
						FeedTrial.set_duration(2000);
						# Need to catch for the first trial, if there is no response
						int respCount = response_manager.response_count();
						int resTime = 0;
						#term.print_line(string(respCount));
						if respCount == 0 then
							resTime = lastStim.time()+3000;
						else
							resTime = lastResp.time();
						end;
						## load the right Pic
						
						#term.print_line(one_Ten[i][1]);
						#term.print_line(one_Ten[i][2]);
						#term.print_line(one_Ten[i][3]);
						#term.print_line(one_Ten[i][l]);
						#term.print("##");
						#term.print_line(picPairs[1][1]);
						#term.print_line(picPairs[1][2]);
						#term.print_line(picPairs[1][3]);
						
						string corrFBpic;
													
						loop int k = 1 until k > picPairsBLK3.count()
						begin
							if picPairsBLK3[k][2] == blk3[i][l] || picPairsBLK3[k][3] == blk3[i][l] || picPairsBLK3[k][4] == blk3[i][l] then
								corrFBpic = picPairsBLK3[k][1];
								break;
							else
								corrFBpic = blk3[i][l];
							end;
							k = k + 1;
						end;
						
						array<string> strParts2[1];
						corrFBpic.split("\\",strParts2);

						presPicFB.set_filename(corrFBpic);
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						
						if resTime > lastStim.time() && resTime <= (lastStim.time() + 2500) then
							
							int deltaTime = 2500 - (resTime - lastStim.time()); # toGo
							stimEvent1.set_event_code("extra Pic Time");
							mainTrial.set_duration(deltaTime);
							mainTrial.set_type(fixed);
							
							mainTrial.present();
							
							
							if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("_i_") != 0) && lastResp.code() == 2) then
								FeedText.set_caption("Richtig, die korrekte Position ist:", true);
								
								FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
								FeedTrial.present();
							else
								FeedText.set_caption("Falsch, die korrekte Position ist:", true);
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
				
					#fixTrial.set_mri_pulse(pulse);
					fixTrial.set_duration(4500);
					fixTrial.present();
					pulse = pulse + 1;
				l = l + 1;

			end;
		blockIndex = blockIndex + 1;
		# Fix 4 pulses
		#loop int f = 1 until f > 4
		#	begin
		#		#fixTrial.set_mri_pulse(pulse);
		#		fixTrial.set_duration(4500);
		#		fixTrial.present();
		#		pulse = pulse +1;
		#		f = f +1;
		#	end;		
		######################################################################
		
	elseif order[masterIndex] == "learning-4" then
	
		#Block4
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			#blk4.shuffle();
			loop int i = 1 until i > blk4.count()
					begin
						
						presPic.set_filename(blk4[i][l]);# set bitmap filename
						
						array<string> strParts[1];
						blk4[i][l].split("\\",strParts);
								
						stimEvent1.set_event_code(  strParts[strParts.count()] + ";block"+string(blockIndex)+ ";LS"+ string(l));
						
						presPic.set_draw_mode(1);
						presPic.load();
					
						if firstTrial then
							mainTrial.set_mri_pulse(pulse);
							firstTrial = false;
						end;
						mainTrial.set_duration(2500);
						mainTrial.set_type(first_response);
						mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						FeedTrial.set_duration(2000);
						# Need to catch for the first trial, if there is no response
						int respCount = response_manager.response_count();
						int resTime = 0;
						#term.print_line(string(respCount));
						if respCount == 0 then
							resTime = lastStim.time()+3000;
						else
							resTime = lastResp.time();
						end;
						## load the right Pic
						
						#term.print_line(one_Ten[i][1]);
						#term.print_line(one_Ten[i][2]);
						#term.print_line(one_Ten[i][3]);
						#term.print_line(one_Ten[i][l]);
						#term.print("##");
						#term.print_line(picPairs[1][1]);
						#term.print_line(picPairs[1][2]);
						#term.print_line(picPairs[1][3]);
						
						string corrFBpic;
													
						loop int k = 1 until k > picPairsBLK4.count()
						begin
							if picPairsBLK4[k][2] == blk4[i][l] || picPairsBLK4[k][3] == blk4[i][l] || picPairsBLK4[k][4] == blk4[i][l] then
								corrFBpic = picPairsBLK4[k][1];
								break;
							else
								corrFBpic = blk4[i][l];
							end;
							k = k + 1;
						end;
						
						array<string> strParts2[1];
						corrFBpic.split("\\",strParts2);

						presPicFB.set_filename(corrFBpic);
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						
						if resTime >lastStim.time() && resTime <= (lastStim.time() + 2500) then
							
							int deltaTime = 2500 - (resTime - lastStim.time()); # toGo
							stimEvent1.set_event_code("extra Pic Time");
							mainTrial.set_duration(deltaTime);
							mainTrial.set_type(fixed);
							
							mainTrial.present();
							
							
							if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("_i_") != 0) && lastResp.code() == 2) then
								FeedText.set_caption("Richtig, die korrekte Position ist:", true);
								
								FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
								FeedTrial.present();
							else
								FeedText.set_caption("Falsch, die korrekte Position ist:", true);
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
				
					#fixTrial.set_mri_pulse(pulse);
					fixTrial.set_duration(4500);
					fixTrial.present();
					pulse = pulse +1;
					
				l = l + 1;
			
		end;
		blockIndex = blockIndex + 1;
		# Fix 4 pulses
		#loop int f = 1 until f > 4
		#	begin
		#		#fixTrial.set_mri_pulse(pulse);
		#		fixTrial.set_duration(4500);
		#		fixTrial.present();
		#		pulse = pulse +1;
		#		f = f +1;
		#	end;		
		######################################################################
	

		
	elseif order[masterIndex] == "control-1" then
	
		#Control - 1
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			ctrl1.shuffle();
			loop int i = 1 until i > ctrl1.count()
					begin
						
						
						int oldRespCount = response_manager.total_response_count();
						presPic.set_filename(ctrl1[i][l]); 														# set bitmap filename
						
						array<string> strParts[1];
						ctrl1[i][l].split("\\",strParts);
								
						#stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
						#presPic.set_draw_mode(1);
						#presPic.load();
					
						####mainTrial.set_mri_pulse(pulse);
						#mainTrial.set_duration(2500);
						#mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						#stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						#response_data lastResp = response_manager.last_response_data();
						
						FeedTrial.set_duration(2500);
						FeedText.set_caption("Ist das Haus auf der rechten Seite?", true);
						presPicFB.set_filename(ctrl1[i][l]);
						FeedEvent1.set_event_code(  strParts[strParts.count()] + ";crt"+string(ctrIndex)+ "-r;LS"+ string(l));
						
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						FeedTrial.present();
						
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						
						int CurrRespCount = response_manager.total_response_count();
						int targetResp = oldRespCount + 1;
						term.print_line(string(targetResp));
						if targetResp < CurrRespCount then
							
							lastResp = response_manager.get_response_data( targetResp );
						else
							lastResp = response_manager.last_response_data();
						end;
						
						
						#left or right?
						
						#array<string> strParts2[1];
						#strParts[strParts.count()].split("_",strParts2);
						
						if lastResp.time() >lastStim.time() && lastResp.time() <= (lastStim.time() + 2500) then
							
							if (strParts[strParts.count()].find("right") != 0) && lastResp.code() == 1  then
								FeedText.set_caption("Richtig, das Haus ist auf der rechten Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("correct;" + strParts[strParts.count()]);
								FeedTrial.present();
							elseif (strParts[strParts.count()].find("left") != 0) && lastResp.code() == 2 then
								FeedText.set_caption("Richtig, das Haus ist nicht auf der rechten Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("correct;" + strParts[strParts.count()]);
								FeedTrial.present();
								
							elseif (strParts[strParts.count()].find("right") != 0) && lastResp.code() == 2  then
								FeedText.set_caption("Falsch, das Haus ist auf der rechten Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("incorrect;" + strParts[strParts.count()]);
								FeedTrial.present();
							elseif (strParts[strParts.count()].find("left") != 0) && lastResp.code() == 1  then
								FeedText.set_caption("Falsch, das Haus ist nicht auf der rechten Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("incorrect;" + strParts[strParts.count()]);
								FeedTrial.present();
							
							end;
							
						else
							
							if strParts[strParts.count()].find("right") != 0 then
								FeedText.set_caption("Zu spät, das Haus ist auf der rechten Seite:", true);
							else
								FeedText.set_caption("Zu spät, das Haus ist nicht auf der rechten Seite:", true);
							end;
							
							FeedEvent1.set_event_code("to late");
							FeedTrial.present();
					
						end;
					
						pulse = pulse +1;
					
						i = i+1;
						
					
					end;
				
					#fixTrial.set_mri_pulse(pulse);
					fixTrial.set_duration(4500);
					fixTrial.present();
					pulse = pulse +1;
					
				l = l + 1;
			
			end;
		ctrIndex = ctrIndex + 1;
		# Fix 4 pulses
		#loop int f = 1 until f > 4
		#	begin
		#		#fixTrial.set_mri_pulse(pulse);
		#		fixTrial.set_duration(4500);
		#		fixTrial.present();
		#		pulse = pulse +1;
		#		f = f +1;
		#	end;
	######################################################################
	elseif order[masterIndex] == "control-2" then
		#Control - 2
		######################################################################
		######################################################################
		loop int l = 1 until l > 4
			begin
			ctrl2.shuffle();
			loop int i = 1 until i > ctrl2.count()
					begin
						int oldRespCount = response_manager.total_response_count();
						presPic.set_filename(ctrl2[i][l]); 														# set bitmap filename
						
						array<string> strParts[1];
						ctrl2[i][l].split("\\",strParts);
								
						#stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
						#presPic.set_draw_mode(1);
						#presPic.load();
					
						####mainTrial.set_mri_pulse(pulse);
						#mainTrial.set_duration(2500);
						#mainTrial.present();
						
						# Feedback
						# Create Feedback depending on Response
						#stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						#response_data lastResp = response_manager.last_response_data();
						
						FeedTrial.set_duration(2500);
						FeedText.set_caption("Ist das Haus auf der linken Seite?", true);
						presPicFB.set_filename(ctrl2[i][l]);
						FeedEvent1.set_event_code(  strParts[strParts.count()] + ";crt"+string(ctrIndex)+ "-l;LS"+ string(l));
						
						presPicFB.set_draw_mode(1);
						presPicFB.load();
						FeedTrial.present();
						
						
						# Feedback
						# Create Feedback depending on Response
						stimulus_data lastStim = stimulus_manager.last_stimulus_data();
						response_data lastResp = response_manager.last_response_data();
						
						
						int CurrRespCount = response_manager.total_response_count();
						int targetResp = oldRespCount + 1;
						term.print_line(string(targetResp));
						if targetResp < CurrRespCount then
							
							lastResp = response_manager.get_response_data( targetResp );
						else
							lastResp = response_manager.last_response_data();
						end;
						
						
						
						#left or right?
						
						#array<string> strParts2[1];
						#strParts[strParts.count()].split("_",strParts2);
						
						if lastResp.time() >lastStim.time() && lastResp.time() <= (lastStim.time() + 2500) then
							
							if (strParts[strParts.count()].find("left") != 0) && lastResp.code() == 1  then
								FeedText.set_caption("Richtig, das Haus ist auf der linken Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("correct;" + strParts[strParts.count()]);
								FeedTrial.present();
							elseif (strParts[strParts.count()].find("right") != 0) && lastResp.code() == 2 then
								FeedText.set_caption("Richtig, das Haus ist nicht auf der linken Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("correct;" + strParts[strParts.count()]);
								FeedTrial.present();
								
							elseif (strParts[strParts.count()].find("left") != 0) && lastResp.code() == 2  then
								FeedText.set_caption("Falsch, das Haus ist auf der linken Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("incorrect;" + strParts[strParts.count()]);
								FeedTrial.present();
							elseif (strParts[strParts.count()].find("right") != 0) && lastResp.code() == 1  then
								FeedText.set_caption("Falsch, das Haus ist nicht auf der linken Seite:", true);
								FeedTrial.set_duration(2000);
								FeedEvent1.set_event_code("incorrect;" + strParts[strParts.count()]);
								FeedTrial.present();
							
							end;
							
						else
							if strParts[strParts.count()].find("left") != 0 then
								FeedText.set_caption("Zu spät, das Haus ist auf der linken Seite:", true);
							else
								FeedText.set_caption("Zu spät, das Haus ist nicht auf der linken Seite:", true);
							end;
							
							FeedEvent1.set_event_code("to late");
							FeedTrial.present();
					
						end;
					
						
						
						
						
						
						## load the right Pic
						
						#term.print_line(one_Ten[i][1]);
						#term.print_line(one_Ten[i][2]);
						#term.print_line(one_Ten[i][3]);
						#term.print_line(one_Ten[i][l]);
						#term.print("##");
						#term.print_line(picPairs[1][1]);
						#term.print_line(picPairs[1][2]);
						#term.print_line(picPairs[1][3]);
						
						#string corrFBpic;
						#							
						#loop int k = 1 until k > picPairs.count()
						#begin
						#	if picPairs[k][2] == blk6[i][l] || picPairs[k][3] == blk6[i][l] then
						#		corrFBpic = picPairs[k][1];
						#		break;
						#	else
						#		corrFBpic = blk6[i][l];
						#	end;
						#	k = k + 1;
						#end;
						#
						#array<string> strParts2[1];
						#corrFBpic.split("\\",strParts2);

						#presPicFB.set_filename(corrFBpic);
						#presPicFB.set_draw_mode(1);
						#presPicFB.load();
						
						#if lastResp.time() >lastStim.time() && lastResp.time() <= (lastStim.time() + 2500) then
						#	
						#	if ((strParts[strParts.count()].find("k") != 0) && lastResp.code() == 1) ||((strParts[strParts.count()].find("_i_") != 0) && lastResp.code() == 2) then
						#		FeedText.set_caption("Richtig, die korrekte Position ist:", true);
						#		
						#		FeedEvent1.set_event_code("correct;" + strParts2[strParts2.count()]);
						#		FeedTrial.present();
						#	else
						#		FeedText.set_caption("Falsch, die korrekte Position ist:", true);
						#		#stimEvent1.set_event_code(  strParts[strParts.count()]+ ";mri_pulse:" + string(pulse));
						#		FeedEvent1.set_event_code("incorrect;" + strParts2[strParts2.count()]);
						#								
						#		FeedTrial.present();
						#	end;
						#	
						#else
					
						#	FeedText.set_caption("Zu spät, die korrekte Position ist:", true);
						#	FeedEvent1.set_event_code("to late");
						#	FeedTrial.present();
					
						#end;
						#
						pulse = pulse +1;
					
						i = i+1;
						
					
					end;
				
					#fixTrial.set_mri_pulse(pulse);
					fixTrial.set_duration(4500);
					fixTrial.present();
					pulse = pulse +1;
					
				l = l + 1;
			
			end;
		ctrIndex = ctrIndex + 1;
		
	end;
	
	
	if exit then
		## Fix 4 pulses between blocks
		loop int f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(hlcb[3]);
				infoPic.set_draw_mode(1);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;
	
	
	masterIndex = masterIndex + 1;
end;

