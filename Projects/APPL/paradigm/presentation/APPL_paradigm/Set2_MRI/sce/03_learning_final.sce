scenario = "fMRI-SET-2";     																								  
default_background_color = 0, 0, 0;
active_buttons = 2;
button_codes = 1,2;  	#1 Pfeil nach links=richtig,2 Pfeil nach rechts =falsch; 3= Leertaste ; 4-6= Tastatur 1,2,3
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
#scan_period = 1000;
pulse_code = 30;
#pulse_width = 6; 

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

int pulse = 4;

array<string> hlcb[4] = {"bubbles/hello.jpg",
								"bubbles/learning.jpg",
								"bubbles/control.jpg",
								"bubbles/bye.jpg"};

###change: element number from 5 to 7 and block 5 & 6 commented
array<string> LEARNINGpics1[7] = {"learning/PICTURE_400.jpg",
											"learning/PICTURE_402.jpg",
											"learning/PICTURE_405.jpg",
											"learning/PICTURE_462.jpg",
											"learning/PICTURE_53.jpg",
											"learning/PICTURE_216.jpg",
											"learning/PICTURE_21.jpg"};
LEARNINGpics1.shuffle();
											
array<string> LEARNINGpics2[7] = {"learning/PICTURE_480.jpg",
											"learning/PICTURE_488.jpg",
											"learning/PICTURE_508.jpg",
											"learning/PICTURE_15.jpg",
											"learning/PICTURE_695.jpg",
											"learning/PICTURE_703.jpg",
											"learning/PICTURE_95.jpg"};
LEARNINGpics2.shuffle();											
											
array<string> LEARNINGpics3[7] = {"learning/PICTURE_576.jpg",
											"learning/PICTURE_581.jpg",
											"learning/PICTURE_52.jpg",
											"learning/PICTURE_594.jpg",
											"learning/PICTURE_297.jpg",
											"learning/PICTURE_23.jpg",
											"learning/PICTURE_605.jpg"};
LEARNINGpics3.shuffle();											
											
array<string> LEARNINGpics4[7] = {"learning/PICTURE_247.jpg",
											"learning/PICTURE_43.jpg",
											"learning/PICTURE_610.jpg",
											"learning/PICTURE_741.jpg",
											"learning/PICTURE_235.jpg",
											"learning/PICTURE_720.jpg",
											"learning/PICTURE_599.jpg"};
LEARNINGpics4.shuffle();											
											
#array<string> LEARNINGpics5[5] = {"learning/PICTURE_53.jpg",
#											"learning/PICTURE_216.jpg",
#											"learning/PICTURE_695.jpg",
#											"learning/PICTURE_703.jpg",
#											"learning/PICTURE_220.jpg"};
#LEARNINGpics5.shuffle();											
#											
#array<string> LEARNINGpics6[5] = {"learning/PICTURE_23.jpg",
#											"learning/PICTURE_235.jpg",
#											"learning/PICTURE_720.jpg",
#											"learning/PICTURE_297.jpg",
#											"learning/PICTURE_746.jpg"};
#LEARNINGpics6.shuffle();


# Load Trials
# 1 Learning Trials
# allPics[Picture, corrW, incorrW1, incorrW2]
###change: element number from 5 to 7 and block 5 & 6 commented
array<string> LEARNINGwords1[7][5] = {{"Lopfer","Loptem","Lopdor","Lopmig","Lopter"},
											{"Resar","Rerod","Regan","Reper","Remert"},
											{"Nomtap","Nomgan","Nomtun","Nomzerl","Nomser"},
											{"Jamip","Jamun","Jakel","Jaser","Jasull"},
											{"Knele","Knera","Knefe","Knetam","Knesam"},
											{"Tignam","Tigfe","Tigdon","Tigdam","Tigmer"},
											{"Krükta","Krükel","Krüktem","Krüklass","Krükmig"}};
LEARNINGwords1.shuffle();												
											
array<string> LEARNINGwords2[7][5] = {{"Zamet","Zate","Zabig","Zabelt","Zatir"},
											{"Jehler","Jehrig","Jehmel","Jehtir","Jehse"},
											{"Zerbe","Zermel","Zerse","Zerpet","Zertock"},
											{"Joten","Joper","Josant","Jotolt","Jota"},
											{"Munem","Muschot","Mufi","Mugir","Mupat"},
											{"Knusap","Knufi","Knufeg","Knupat","Knuler"},
											{"Klenter","Klentant","Klenban","Klenta","Klenfalt"}};
LEARNINGwords2.shuffle();												
											
array<string> LEARNINGwords3[7][5] = {{"Schöle","Schölte","Schölse","Schölme","Schölter"},
											{"Zampe","Zamse","Zamram","Zambel","Zamler"},
											{"Geiten","Geibel","Geiner","Geiper","Geitel"},
											{"Gürbas","Gürzer","Gürter","Gürbel","Gürse"},
											{"Eume","Eupis","Euko","Eudet","Eutaf"},
											{"Koptan","Koptel","Koptur","Kopster","Kopsel"},
											{"Kegan","Ketan","Ketosch","Keton","Keteik"}};
LEARNINGwords3.shuffle();												
											
array<string> LEARNINGwords4[7][5] = {{"Stise","Stitons","Stisin","Stigit","Stisum"},
											{"Finser","Finsin","Finlas","Finsum","Finges"},
											{"Seise","Seimer","Seitos","Seiges","Seitu"},
											{"Soktau","Soklet","Soktal","Sokma","Sokbat"},
											{"Efdi","Efter","Efto","Efser","Efnel"},
											{"Tulser","Tulte","Tulpos","Tulber","Tuldet"},
											{"Klotel","Klosal","Klotons","Klobat","Kloger"}};
LEARNINGwords4.shuffle();												
											
#array<string> LEARNINGwords5[5][5] = {{"Knelle","Lennrak","Kneupfe","Stuktat","Terdam"},
#											{"Tignam","Kneupfe","Knoschot","Terdam","Megir"},
#											{"Munem","Knoschot","Mofi","Megir","Trampat"},
#											{"Knucknap","Mofi","Mifeg","Trampat","Treelet"},
#											{"Knüjatt","Mifeg","Lennrak","Treelet","Stuktat"}};
#LEARNINGwords5.shuffle();	
#											
#array<string> LEARNINGwords6[5][5] = {{"Kopran","Knustel","Kollter","Eschdel","Tursen"},
#											{"Efdi","Kollter","Tonte","Tursen","Ennel"},
#											{"Tulser","Tonte","Kropis","Ennel","Eidet"},
#											{"Eume","Kropis","Emkor","Eidet","Tummhaft"},
#											{"Trelle","Emkor","Knustel","Tummhaft","Eschdel"}};
#LEARNINGwords6.shuffle();	

###change: element number from [30][6] decreased to [28][8]. From i>5 to i>7 and block 5 & 6 commented
#question?????
array<string> LEARNING[28][8];

loop int i=1 until i>7
begin
	LEARNING[i][1] = LEARNINGpics1[i];
	LEARNING[i][2] = LEARNINGwords1[i][1];
	LEARNING[i][3] = LEARNINGwords1[i][2];
	LEARNING[i][4] = LEARNINGwords1[i][3];
	LEARNING[i][5] = LEARNINGwords1[i][4];
	LEARNING[i][6] = LEARNINGwords1[i][5];
	
	LEARNING[i+7][1] = LEARNINGpics2[i];
	LEARNING[i+7][2] = LEARNINGwords2[i][1];
	LEARNING[i+7][3] = LEARNINGwords2[i][2];
	LEARNING[i+7][4] = LEARNINGwords2[i][3];
	LEARNING[i+7][5] = LEARNINGwords2[i][4];
	LEARNING[i+7][6] = LEARNINGwords2[i][5];
	
	LEARNING[i+14][1] = LEARNINGpics3[i];
	LEARNING[i+14][2] = LEARNINGwords3[i][1];
	LEARNING[i+14][3] = LEARNINGwords3[i][2];
	LEARNING[i+14][4] = LEARNINGwords3[i][3];
	LEARNING[i+14][5] = LEARNINGwords3[i][4];
	LEARNING[i+14][6] = LEARNINGwords3[i][5];
	
	LEARNING[i+21][1] = LEARNINGpics4[i];
	LEARNING[i+21][2] = LEARNINGwords4[i][1];
	LEARNING[i+21][3] = LEARNINGwords4[i][2];
	LEARNING[i+21][4] = LEARNINGwords4[i][3];
	LEARNING[i+21][5] = LEARNINGwords4[i][4];
	LEARNING[i+21][6] = LEARNINGwords4[i][5];
	
	#LEARNING[i+20][1] = LEARNINGpics5[i];
	#LEARNING[i+20][2] = LEARNINGwords5[i][1];
	#LEARNING[i+20][3] = LEARNINGwords5[i][2];
	#LEARNING[i+20][4] = LEARNINGwords5[i][3];
	#LEARNING[i+20][5] = LEARNINGwords5[i][4];
	#LEARNING[i+20][6] = LEARNINGwords5[i][5];
	
	#LEARNING[i+25][1] = LEARNINGpics6[i];
	#LEARNING[i+25][2] = LEARNINGwords6[i][1];
	#LEARNING[i+25][3] = LEARNINGwords6[i][2];
	#LEARNING[i+25][4] = LEARNINGwords6[i][3];
	#LEARNING[i+25][5] = LEARNINGwords6[i][4];
	#LEARNING[i+25][6] = LEARNINGwords6[i][5];
	
	i = i + 1;

#question?????
end;
###Change: 5 & 6 commented
#CHECK!!!!
loop int i=1 until i>LEARNING.count()
begin
	term.print_line(LEARNING[i][1] + " - " + LEARNING[i][2] + " - " + LEARNING[i][3] + " - " + LEARNING[i][4]); #+ " - " + LEARNING[i][5] + " - " + LEARNING[i][6]);
	i = i + 1;
end;



###Change: Element number from 20 to 28
array<string> CONTROL[28][4] =  {{"control/PICTURE_2.jpg","Reifen","Tiger","Kompass"},
											{"control/PICTURE_98.jpg","Tiger","Kompass","Gewehr"},
											{"control/PICTURE_292.jpg","Kompass","Gewehr","Tunnel"},
											{"control/PICTURE_645.jpg","Gewehr","Tunnel","Reifen"},
											{"control/PICTURE_286.jpg","Tunnel","Reifen","Tiger"},
											{"control/PICTURE_733.jpg","Brille","Vogel","Wolle"},
											{"control/PICTURE_430.jpg","Vogel","Wolle","Hose"},
											{"control/PICTURE_134.jpg","Wolle","Hose","Bagger"},
											{"control/PICTURE_718.jpg","Hose","Bagger","Brille"},
											{"control/PICTURE_746.jpg","Kegel","Möwe","Flagge"},
											{"control/PICTURE_220.jpg","Möwe","Flagge","Blume"},
											{"control/PICTURE_295.jpg","Flagge","Blume","Kegel"},
											{"control/PICTURE_312.jpg","Blume","Kegel","Möwe"},
											{"control/PICTURE_731.jpg","Bagger","Brille","Vogel"},
											{"control/PICTURE_549.jpg","Schlange","Parfüm","Bibel"},
											{"control/PICTURE_314.jpg","Parfüm","Bibel","Tasche"},
											{"control/PICTURE_350.jpg","Bibel","Tasche","Vorhang"},
											{"control/PICTURE_388.jpg","Tasche","Vorhang","Schlange"},
											{"control/PICTURE_418.jpg","Vorhang","Schlange","Parfüm"},
											{"control/PICTURE_476.jpg","Schürze","Nagel","Apfel"},
											{"control/PICTURE_485.jpg","Nagel","Apfel","Tasse"},
											{"control/PICTURE_552.jpg","Apfel","Tasse","Säule"},
											{"control/PICTURE_498.jpg","Tasse","Säule","Schürze"},
											{"control/PICTURE_386.jpg","Bombe","Maske","Spiegel"},
											{"control/PICTURE_84.jpg","Maske","Spiegel","Schlitten"},
											{"control/PICTURE_340.jpg","Spiegel","Schlitten","Bombe"},
											{"control/PICTURE_625.jpg","Schlitten","Bombe","Maske"},
											{"control/PICTURE_663.jpg","Säule","Schürze","Nagel"}};
											
											
							
											

# [Trial, LS]
###change: trial from 10 to 14 and 5 & 6 commented. ctrll from 20 to 28
array<string> blk1[14][4];
array<string> blk2[14][4];
array<string> blk3[14][4];
array<string> blk4[14][4];
#array<string> blk5[10][4];
#array<string> blk6[10][4];

array<string> ctrl1[28][4];
array<string> ctrl2[28][4];

#question?????
int a = 1;
int b = 1;
int c = 1;
int d = 1;
int e = 1;
int f = 1;

###change: trial from 40 to 42
# dict. with all correct pairs
array<string> allCorrPairs[42][2];

#int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Marcus/A/Stimuli",  allPics );

###change: trial from 40 to 42
##### extra Function please no Questions

sub string getRightName(string pic)
begin
	loop int i = 1 until i > 42
	begin
		if pic == allCorrPairs[i][1] then
			
			return allCorrPairs[i][2];
		end;
	i = i + 1;
	end;

	return "-1";
	
end;

#question?????
#Make Blocks
###change: element number adjusted e.g. (i<=5) to (i<=7). 5 & 6 blocks commented
loop int i = 1 until i > LEARNING.count()
	begin
		if (i<=7) then	# Block 1
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
		elseif(i>7) && (i<=14) then	# Block 2
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
		elseif(i>14) && (i<=21) then	# Block 3
			# learning 1
			blk3[c][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk3[c][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][2] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk3[c][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][3] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk3[c][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			c = c + 2;	
		elseif(i>21) && (i<=28) then	# Block 4
			# learning 1
			blk4[d][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk4[d][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk4[d][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk4[d][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			d = d + 2;
		#elseif(i>20) && (i<=25) then	# Block 5
			# learning 1
			#blk5[e][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			#blk5[e][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			#blk5[e][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			#blk5[e][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			#e = e + 2;
		#elseif(i>25) && (i<=30) then	# Block 6
			# learning 1
			#blk6[f][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			#blk6[f][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			#blk6[f][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			#blk6[f][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			#f = f + 2;
		end;
		i = i+1;
	end;

a = 1;
b = 1;

###changed: trial from 10 to 14
#CONTROL.shuffle();
loop int i = 1 until i > CONTROL.count() 
begin
	if i<=14 then
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
		
	else
		# learning 1
		ctrl2[b][1] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl2[b+1][1] = CONTROL[i][1] + ";" + CONTROL[i][3] + ";" + CONTROL[i][2] + ";i";
		# learning 2
		ctrl2[b][2] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl2[b+1][2] = CONTROL[i][1] + ";" + CONTROL[i][4] + ";" + CONTROL[i][2] + ";i";
		# learning 3
		ctrl2[b][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2]+ ";" + CONTROL[i+1][2] + ";c";
		ctrl2[b+1][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][3] + ";" + CONTROL[i+1][2] + ";i";
		# learning 4
		ctrl2[b][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl2[b+1][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][4] + ";" + CONTROL[i+1][2] + ";i";
		b = b + 2;
		
	end;
	i = i + 2;
end;

# Check Trial Train.
###changed: blocks from 8 to 6  and trials from 10 to 14. blk 5 & 6 commented
array<int> BlockOrder[] = {1,2,3,4,5,6}; ## 7 = Contro-1 and 8 = Control-2 

array<string> Task_List[6][4][14];

loop int blk = 1 until blk > 6
begin
	loop int ls = 1 until ls > 4
	begin
		loop int item = 1 until item > 14
		begin
			# Blocks
			if blk == 1 then
				Task_List[blk][ls][item] = blk1[item][ls];
			elseif blk == 2 then
				Task_List[blk][ls][item] = blk2[item][ls];
			elseif blk == 3 then
				Task_List[blk][ls][item] = blk3[item][ls];
			elseif blk == 4 then
				Task_List[blk][ls][item] = blk4[item][ls];
			#elseif blk == 5 then
				#Task_List[blk][ls][item] = blk5[item][ls];
			#elseif blk == 6 then
				#Task_List[blk][ls][item] = blk6[item][ls];
			elseif blk == 5 then	#Control-Block
				Task_List[blk][ls][item] = ctrl1[item][ls];
			elseif blk == 6 then #Control-Block
				Task_List[blk][ls][item] = ctrl2[item][ls];
			end;
			item = item + 1;
		end;
		
		## Shuffle lStage Items
		###changed: 10 to 14
		array<string> dummy[14];
		bool isOK = false;
		loop until isOK
		begin
			dummy = Task_List[blk][ls];
			dummy.shuffle();
			Task_List[blk][ls] = dummy;
			loop int k = 1 until k > 13
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
###changed: block number adjusted
int isOrderOK = 0;
loop until isOrderOK == 1
begin
	BlockOrder.shuffle();
	isOrderOK = 1;
	loop int x = 2 until x > BlockOrder.count()
	begin
		if BlockOrder[1] == 5 || BlockOrder[1] == 6 || BlockOrder[6] == 5 || BlockOrder[6] == 6 || (BlockOrder[x-1] == 5 && BlockOrder[x] == 6) || (BlockOrder[x-1] == 6 && BlockOrder[x] == 5) then
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
string introText = "Das Experiment\nbeginnt gleich.\n\nZu Erinnerung: \n   Ja = Zeigefinger\n Nein = Daumen";

FeedText.set_caption(introText, true);
FeedEvent.set_event_code("Hello - Intro");
FeedTrial.set_duration(100);
#FeedTrial.set_type(first_response);
FeedTrial.present();

bool firstTrial = true;
#Block 1 to 4
###changed: block number from 8 to 6
loop int blk = 1 until blk > 6
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
	###changed: block number adjusted
	string infoBubble = "";
	string infoBubble2 = "";
	bool exit = false;
	if currBlk == 5 || currBlk == 6 then
		infoBubble = hlcb[3];	# Control
	elseif  blk == 6 && (currBlk == 1 || currBlk == 2 || currBlk == 3 || currBlk == 4) then
		infoBubble = hlcb[2];	# learning
		infoBubble2 = hlcb[4];	# bye
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
				InfoEvent.set_event_code(infoBubble);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;
	
	###changed: 10 to 14
	loop int ls = 1 until ls > 4
	begin
		loop int i = 1 until i > 14
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
				infoPic.set_filename(infoBubble2);
				infoPic.set_draw_mode(1);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;		
	
	
blk = blk + 1;
end;




