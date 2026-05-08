####Learning Development fMRI LOCATO########
##Sham-sham arm ## 
# by Mohamed Abdelmotaleb
#R version 4.0.5 (2021-03-31) -- "Shake and Throw"


rm(list = ls())


library(dplyr)
library(psycho)
library(tidyverse)
library(openxlsx)
library(data.table)
library(stringr)


setwd("Y:/01_Studien/00_FOR5429_MeMoSLAP/RU_Experiments_Participants/12_TaskLogfiles/P1/Sham-Sham/Main_Task_last")


filenames <- list.files(pattern="*log", full.names=T)

print(filenames)


df1 <- filenames %>%
  map_df(read.table,  sep="\t", header=TRUE, na.strings =  " ", fill=TRUE, skip=3)



############# done read all learning files of the long version #####


####working with the data set ##########

# t/time infront of the previous response event.type is the reaction time
# variable: "Code" contains information whether the response was correct/ incorrect/ too late
#h88_p16_i_down.jpg;block1;LS1 (block_stage) -> gives information of learning stage and block
#Picture	correct;h88_p35_k_down.jpg (feedback) -> gives information regarding the response of the participant 

#keep only relevant rows (Picture) ; because the Response is included within the feedback
df1 <- df1%>%
  filter(!(Code == "extra Pic Time"))


# Create a logical vector that identifies rows containing 'correct', 'incorrect', or 'tolate' in the 'Code' column
df1$RT <- NA  # Initialize the RT column



# Loop through each row
for (i in 2:nrow(df1)) {
  # Check if the Code column contains 'correct', 'incorrect', or 'tolate'
  if (grepl("correct|incorrect", df1$Code[i])) {
    
    # Find the last 'Response' event type before the current row
    prev_response_idx <- max(which(df1$Event.Type[1:(i-1)] == 'Response'))
    
    # If such a row exists, assign its TTime to the RT column
    if (length(prev_response_idx) > 0) {
      df1$RT[i] <- df1$TTime[prev_response_idx]
    }
  }
}



df2 <- df1 %>% filter(Event.Type %in% c("Picture"))

#drop fixation, drop instructions
df2 <- df2 %>%
  filter(!(Code == "fix")) %>%
  filter(!grepl("bubbles", Code)) %>%
  filter(!(Code == "Hello - Intro"))

#create new variable (block)
df3 <- df2 %>%
  group_by(Subject) %>%
  mutate(Block = case_when(
    grepl("block1", Code) ~ "1",
    grepl("block2", Code) ~ "2",
    grepl("block3", Code) ~ "3",
    grepl("block4", Code) ~ "4",
    grepl("block5", Code) ~ "5",
    grepl("block6", Code) ~ "6",
    grepl("crt1", Code) ~ "c1",
    grepl("crt2", Code) ~ "c2"))

df3 <- df3 %>%
  group_by(Subject) %>%
  fill(Block, .direction = "down")

#create new variable Stage
df3 <- df3 %>%
  group_by(Block) %>%
  mutate(Stage = case_when(
    grepl("LS1", Code) ~ "1",
    grepl("LS2", Code) ~ "2",
    grepl("LS3", Code) ~ "3",
    grepl("LS4", Code) ~ "4"))

df3$Task_Type = ifelse(grepl(c("c"), df3$Block), "control", "learning")


df3 <- df3 %>%
  group_by(Subject) %>%
  fill(Stage, .direction = "down")


#create new variable Block_Stage
df3$Block_Stage <- with(df3, paste(Block, Stage, sep = "_"))


# done forming the structure of for the analyses ##########


df4 <- df3 %>%
  filter(!grepl("block", Code)) %>%
  filter(!grepl("LS", Code))

#all these previous codes is to keep only the "feedback" rows to make the analysis of the correctness

#### calculate number of correct responses
#get correct, incorrect, to late
df4$Response <- gsub(";.*","",df4$Code)


df5 <- df4 %>%
  mutate(Response_num = case_when(Response == "correct" ~ '1',
                                  Response == "incorrect" ~ '0',
                                  Response == "to late" ~ '0'))

df5$Response_num <- as.numeric(df5$Response_num)

#extract the session(out of naming)
#sub001p1_s3_task1 (session 3, from subject 001)
df5 <- df5 %>%
  mutate(Session = case_when(
    grepl("s3", Subject, ignore.case=T) ~ "3",
    grepl("s4", Subject, ignore.case=T) ~ "4"))


## consider Presentation's way of formating Reaction Time (0.1 ms)
df5$RT <- as.numeric(df5$RT)
df5$RT <- (df5$RT/10000)

# Calculate the mean of Response_num for each Stage for each Subject across blocks

df5_learning <- df5 %>%
  filter(Block %in% 1:6) %>%
  group_by(Subject, Stage) %>%
  summarize (mean_learning_response = round(mean(Response_num, na.rm = TRUE)*100,2),
             sd_learning_response= round(sd(Response_num,na.rm = TRUE)*100,2)) %>%
  ungroup()


# Calculate the mean of Response_num for each Stage for each Subject across blocks
df5_control <- df5 %>%
  filter(Block %in% c('c1', 'c2')) %>%
  group_by(Subject, Stage) %>%
  summarize(mean_control_response = round(mean(Response_num, na.rm = TRUE)*100,2 ),
            sd_control_response= round(sd(Response_num, na.rm = TRUE)*100,2)) %>%
  ungroup()


# Merge the mean and standard deviation values with the original data frame
df5 <- df5 %>%
  left_join(df5_learning, by = c("Subject", "Stage"), suffix = c("", "_learning")) %>%
  left_join(df5_control, by = c("Subject", "Stage"), suffix = c("", "_control")) %>%
  mutate(
    mean_response_stage = case_when(
      Task_Type == "learning" ~ mean_learning_response,
      Task_Type == "control" ~ mean_control_response
    ),
    sd_response_stage = case_when(
      Task_Type == "learning" ~ sd_learning_response,
      Task_Type == "control" ~ sd_control_response
    )
  ) %>%
  select(-mean_learning_response, -mean_control_response, -sd_learning_response, -sd_control_response) # Remove the intermediate columns


#If you want the mean of each stage in each block
#df5 <- df5 %>%
#group_by(Subject,Block,Stage) %>%
#mutate(mean_Response_block = round(mean(Response_num, na.rm = TRUE)*100,2 )) %>% 
#ungroup()

#df5 <- df5 %>%
#group_by(Subject,Block,Stage) %>%
#mutate(mean_Response_block = round(mean(Response_num, na.rm = TRUE)*100,2 )) %>% 
#ungroup()

#RT
df5_learning_RT <- df5 %>%
  filter(Block %in% 1:6) %>%
  group_by(Subject, Stage) %>%
  summarize (mean_learning_RT = round(mean(RT, na.rm = TRUE),2),
             sd_learning_RT= round(sd(RT,na.rm = TRUE),2)) %>%
  ungroup()


# Calculate the mean of Response_num for each Stage of each control block for each Subject
df5_control_RT <- df5 %>%
  filter(Block %in% c('c1', 'c2')) %>%
  group_by(Subject, Stage) %>%
  summarize(mean_control_RT = round(mean(RT, na.rm = TRUE),2),
            sd_control_RT= round(sd(RT,na.rm = TRUE),2)) %>%
  ungroup()

# Merge the mean values with the original data frame
df5 <- df5 %>%
  left_join(df5_learning_RT, by = c("Subject", "Stage"), suffix = c("", "_learning")) %>%
  left_join(df5_control_RT, by = c("Subject", "Stage"), suffix = c("", "_control")) %>%
  mutate(
    mean_RT_stage = case_when(
      Task_Type == "learning" ~ mean_learning_RT,
      Task_Type == "control" ~ mean_control_RT
    ),
    sd_RT_stage = case_when(
      Task_Type == "learning" ~ sd_learning_RT,
      Task_Type == "control" ~ sd_control_RT
    )
  ) %>%
  select(-mean_learning_RT, -mean_control_RT, -sd_learning_RT, -sd_control_RT) # Remove the intermediate columns

#df5 <- df5 %>%
#group_by(Stage) %>%
#mutate(mean_RT = round(mean(RT, na.rm = TRUE), 3)) %>%
#ungroup()

df5$ID <- gsub("p.*","",df5$Subject)
df5$ID <- gsub("[^0-9.]", "",df5$ID)

# split Subject column into information like subject, session and task
df5 <- df5 %>% separate(Subject, into = c("Subject_", "Session", "Task"), sep = "_", remove = FALSE)

# Select only the relevant columns
df_summarized <- df5 %>%
  select(Subject, ID, Task, Session, Stage, Task_Type, mean_response_stage, sd_response_stage, mean_RT_stage, sd_RT_stage)

# Select distinct rows based on ID, Task_Type, Session, and Stage
df_unique <- df_summarized %>%
  distinct(ID, Task_Type, Session, Stage, .keep_all = TRUE)
df_unique$Task <- gsub("task", "", df_unique$Task)
df_unique$Session <- gsub("s", "", df_unique$Session)


#df5$Subject_ <- gsub("sub", "sub-", df5$Subject_)
#df5$Subject_ <- gsub("p1", "", df5$Subject_)
#df5$Session <- gsub("s", "ses-", df5$Session)
#df5$Task <- gsub("task", "", df5$Task)

write.csv(df_unique,"Y:/01_Studien/00_FOR5429_MeMoSLAP/RU_RegularMeetings/JF_Mohamed_P1/others/Behavioral analysis-/data.csv", row.names = FALSE) 



############### Gettig the mean over stages in learning and control tasks##############################
library(dplyr)
library(stringr)

# Example: clean df_control (do the same for df_learning)

df_control_clean <- df5_control %>%
  # Extract subject ID (sub001, sub002, etc.)
  mutate(Subject_ID = str_extract(Subject, "sub\\d+")) %>%
  
  # Extract session info (s3, s4, etc.)
  mutate(Session = str_extract(Subject, "s\\d+")) %>%
  
  # (Optional) extract Task info if useful
  mutate(Task = str_extract(Subject, "task\\d+")) %>%
  
  # Reorder columns for clarity
  select(Subject, Subject_ID, Session, Task, everything())

# Now compute mean over stages (grouped by Subject_ID and Session)
df_control_summary <- df_control_clean %>%
  group_by(Subject_ID, Session) %>%
  summarise(
    mean= mean(mean_control_response, na.rm = TRUE),
    .groups = "drop"
  )

# Do the same for df_learning :
df_learning_clean <- df5_learning %>%
  mutate(Subject_ID = str_extract(Subject, "sub\\d+"),
         Session = str_extract(Subject, "s\\d+"),
         Task = str_extract(Subject, "task\\d+")) %>%
  select(Subject, Subject_ID, Session, Task, everything())


# Now compute mean over stages (grouped by Subject_ID and Session)
df_learning_summary <- df_learning_clean %>%
  group_by(Subject_ID, Session) %>%
  summarise(
    mean= mean(mean_learning_response, na.rm = TRUE),
    .groups = "drop"
  )

write.csv(df_learning_summary,"Y:/01_Studien/00_FOR5429_MeMoSLAP/RU_RegularMeetings/JF_Mohamed_P1/others/Behavioral analysis-/data_learning_Stages.csv", row.names = FALSE) 
write.csv(df_control_summary,"Y:/01_Studien/00_FOR5429_MeMoSLAP/RU_RegularMeetings/JF_Mohamed_P1/others/Behavioral analysis-/data_control_stages.csv", row.names = FALSE) 


out_dir <- "Y:/01_Studien/00_FOR5429_MeMoSLAP/RU_RegularMeetings/JF_Mohamed_P1/others/Behavioral analysis-"

readr::write_csv(df5,    file.path(out_dir, "df5.csv"))
readr::write_tsv(df5,    file.path(out_dir, "df5.tsv"))
readr::write_csv(df_unique, file.path(out_dir, "df_unique.csv"))

##########################################################################################################
######################  Compute behavioral parameters (with stage columns)  ##############################
##########################################################################################################

library(dplyr)
library(tidyr)
library(stringr)

# ------------------------
# Parameters
# ------------------------
# ⬇️ Edit this list when you want to exclude subjects; leave as c() for none
exclude_subjects <- c("sub012")   # e.g., c("sub012","sub045")
save_csv <- TRUE

out_dir  <- "C:/Users/abdelmotalem/Downloads/Behavioral Data/sham-sham arm/2_Behavioural_analysis_descriptives"
out_wide <- file.path(out_dir, "behavioral_parameters.csv")
out_long <- file.path(out_dir, "behavioral_parameters_long_stages.csv")

# ------------------------
# Prepare data
# Assumes you have a data.frame `df5_learning` with columns:
#   Subject, Stage (1–4 for learning), mean_learning_response
# ------------------------
df_clean <- df5_learning %>%
  mutate(
    Stage       = as.numeric(Stage),
    BaseSubject = str_extract(tolower(Subject), "sub\\d+")
  )

# ------------------------
# 1) Stage means (learning stages 1–4)
#    Produces Stage1..Stage4, and Python-friendly L1..L4 columns.
# ------------------------
df_stage_summary <- df_clean %>%
  filter(Stage %in% 1:4) %>%
  group_by(BaseSubject, Stage) %>%
  summarise(mean_stage_response = mean(mean_learning_response, na.rm = TRUE), .groups = "drop") %>%
  mutate(Stage = paste0("Stage", Stage)) %>%
  tidyr::pivot_wider(
    names_from = Stage, values_from = mean_stage_response
  ) %>%
  mutate(
    L1_accuracy = Stage1,
    L2_accuracy = Stage2,
    L3_accuracy = Stage3,
    L4_accuracy = Stage4
  )

# ------------------------
# 2) Averages & simple contrasts
# ------------------------
df_stage_diffs <- df_stage_summary %>%
  mutate(
    avg_accuracy        = rowMeans(dplyr::across(c(Stage1, Stage2, Stage3, Stage4)), na.rm = TRUE),
    Stage4_minus_Stage1 = Stage4 - Stage1,
    Stage3_minus_Stage1 = Stage3 - Stage1,
    Stage3_minus_Stage2 = Stage3 - Stage2,
    Stage4_minus_Stage2 = Stage4 - Stage2
  )

# ------------------------
# 3) Learning slope + baseline (Stage1)
# ------------------------
df_stage_avg_long <- df_clean %>%
  filter(Stage %in% 1:4) %>%
  group_by(BaseSubject, Stage) %>%
  summarise(mean_learning_response = mean(mean_learning_response, na.rm = TRUE), .groups = "drop")

df_slope <- df_stage_avg_long %>%
  group_by(BaseSubject) %>%
  summarise(
    Stage1_accuracy = mean_learning_response[Stage == 1],
    learning_slope  = if (sum(!is.na(mean_learning_response)) >= 2)
      coef(lm(mean_learning_response ~ Stage))[2] else NA_real_,
    .groups = "drop"
  )

# ------------------------
# 4) Merge everything
# ------------------------
df_all_params <- df_stage_diffs %>%
  inner_join(df_slope, by = "BaseSubject")

# ------------------------
# 5) Apply exclusions (simple vector), order, and final columns
#     subject_id is kept as BaseSubject to match your CONN IDs.
# ------------------------
exclude_subjects <- tolower(exclude_subjects)

df_final <- df_all_params %>%
  filter(!BaseSubject %in% exclude_subjects) %>%
  arrange(BaseSubject) %>%
  mutate(subject_id = BaseSubject) %>%
  select(
    subject_id,
    # Python per-stage columns:
    L1_accuracy, L2_accuracy, L3_accuracy, L4_accuracy,
    # Summary metrics:
    avg_accuracy, Stage1_accuracy, learning_slope,
    # Optional contrasts:
    Stage4_minus_Stage1, Stage3_minus_Stage1, Stage3_minus_Stage2, Stage4_minus_Stage2
  )

# ------------------------
# 6) Optional: long format (subject × stage) for QA/plots
# ------------------------
df_long <- df_final %>%
  select(subject_id, L1_accuracy, L2_accuracy, L3_accuracy, L4_accuracy) %>%
  pivot_longer(cols = starts_with("L"),
               names_to = "stage_label", values_to = "accuracy") %>%
  mutate(stage = as.integer(stringr::str_extract(stage_label, "\\d+"))) %>%
  arrange(subject_id, stage) %>%
  select(subject_id, stage, accuracy)

# ------------------------
# 7) Inspect and save
# ------------------------
print(df_final)

if (save_csv) {
  dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
  write.csv(df_final, out_wide, row.names = FALSE)
  write.csv(df_long, out_long, row.names = FALSE)
  message("Saved: ", out_wide)
  message("Saved (long): ", out_long)
}
