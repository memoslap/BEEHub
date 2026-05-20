############################################################################################
#########################Last ICC used in the paper ########################################
############################################################################################
############################################################################################
############################################################################################
################## adjust the type of ICC in each step #####################################
############################################################################################

rm(list = ls())


library(irr)
library(psych)
library(dplyr)
library(tidyr)
library(ggplot2)



#analysing data at the stage level

#we are importing data block but we will exctract and analyse the stages only from it
data <- read.csv("C:/Users/abdelmotalem/Downloads/Behavioral Data/sham-sham arm/data_block.csv")


# Aggregate the data to get the mean Response_num for each Stage, Task_Type, and Session
aggregated_data <- data %>%
  group_by(ID, Task_Type, Stage, Session) %>%
  summarize(mean_accuracy = mean(Response_num)) %>%
  ungroup()


# Reshape the data to wide format with separate columns for Session3 and Session4
wide_data <- aggregated_data %>%
  spread(key = Session, value = mean_accuracy)


# Rename columns for clarity
colnames(wide_data)[4:5] <- c("Session3", "Session4")



# Calculate ICC for each Task_Type and Stage
icc_results_accuracy <- icc(wide_data[, c("Session3", "Session4")], 
                  model = "twoway", 
                  type = "agreement", 
                  unit = "single")


# View the ICC results
print(icc_results_accuracy)


##############################################################################################################
#Reaction time (RT)
# Aggregate the data to get the mean RT for each Stage, Task_Type, and Session
aggregated_data_RT <- data %>%
  group_by(ID, Task_Type, Stage, Session) %>%
  summarize(mean_RT = mean(RT, na.rm = TRUE)) %>%
  ungroup()



# Reshape the data to wide format with separate columns for Session3 and Session4
wide_data_RT <- aggregated_data_RT %>%
  spread(key = Session, value = mean_RT)


# Rename columns for clarity
colnames(wide_data_RT)[4:5] <- c("Session3", "Session4")




# Calculate ICC for each Task_Type and Stage
icc_results_RT <- icc(wide_data_RT [, c("Session3", "Session4")], 
                  model = "twoway", 
                  type = "agreement", 
                  unit = "single")


##############################################################################################################
##############################################################################################################
##############################################################################################################

# View the ICC results
print(icc_results_RT)



##############################################################################################################
# Filter data to keep only the learning blocks and mean accuracy by participant, task, and session

##accurancy data## 

##learning task only## 

accuracy_data <- data %>%
  filter(Task_Type == "learning") %>%
  group_by(ID, Stage, Session) %>%
  summarize(mean_accuracy = mean(Response_num)) %>%
  spread(key = Session, value = mean_accuracy)


# Rename columns for clarity
colnames(accuracy_data)[3:4] <- c("Session3", "Session4")


icc_result_accurancy_learning <- icc(accuracy_data[, c("Session3", "Session4")], 
                  model = "twoway", 
                  type = "agreement", 
                  unit = "single")

print(icc_result_accurancy_learning)


##control task only ## 

# Filter data to keep only the learning blocks and mean accuracy by participant, task, and session
accuracy_data_control <- data %>%
  filter(Task_Type == "control") %>%
  group_by(ID, Stage, Session) %>%
  summarize(mean_accuracy = mean(Response_num)) %>%
  spread(key = Session, value = mean_accuracy)


# Rename columns for clarity
colnames(accuracy_data_control)[3:4] <- c("Session3", "Session4")


icc_result_accuracy_control <- icc(accuracy_data_control[, c("Session3", "Session4")], 
                           model = "twoway", 
                           type = "agreement", 
                           unit = "single")

print(icc_result_accuracy_control)





##############################################################################################################


##reaction time##



##learning task only## 
# Filter data to keep only the learning blocks and mean RT by participant, task, and session
RT_data <- data %>%
  filter(Task_Type == "learning") %>%
  group_by(ID, Stage, Session) %>%
  summarize(mean_RT = mean(RT,na.rm = TRUE)) %>%
  spread(key = Session, value = mean_RT)


# Rename columns for clarity
colnames(RT_data)[3:4] <- c("Session3", "Session4")


icc_result_RT_learning <- icc(RT_data[, c("Session3", "Session4")], 
                                     model = "twoway", 
                                     type = "agreement", 
                                     unit = "single")

print(icc_result_RT_learning)


##control task only ## 

# Filter data to keep only the control blocks and mean RT by participant, task, and session
RT_data_control <- data %>%
  filter(Task_Type == "control") %>%
  group_by(ID, Stage, Session) %>%
  summarize(mean_RT_control = mean(RT,na.rm = TRUE)) %>%
  spread(key = Session, value = mean_RT_control)


# Rename columns for clarity
colnames(RT_data_control)[3:4] <- c("Session3", "Session4")


icc_result_RT_control <- icc(RT_data_control[, c("Session3", "Session4")], 
                              model = "twoway", 
                              type = "agreement", 
                              unit = "single")

print(icc_result_RT_control)




##############################################################################################################

#another method for analysing data at the stage  level- the same results

##############################################################################################################
##############################################################################################################


# Sample ICC data (replace with actual extracted values)
icc_data <- data.frame(
  Task = c("Accuracy", "Accuracy", "RT", "RT", "Accuracy", "RT"),
  Condition = c("Learning", "Control", "Learning", "Control", "overall", "overall"),
  ICC = c(
    icc_result_accurancy_learning$value,
    icc_result_accuracy_control$value,
    icc_result_RT_learning$value,
    icc_result_RT_control$value,
    icc_results_accuracy$value,  # General ICC for accuracy
    icc_results_RT$value  # General ICC for reaction time
  ),
  LowerCI = c(
    icc_result_accurancy_learning$lbound,
    icc_result_accuracy_control$lbound,
    icc_result_RT_learning$lbound,
    icc_result_RT_control$lbound,
    icc_results_accuracy$lbound,
    icc_results_RT$lbound
  ),
  UpperCI = c(
    icc_result_accurancy_learning$ubound,
    icc_result_accuracy_control$ubound,
    icc_result_RT_learning$ubound,
    icc_result_RT_control$ubound,
    icc_results_accuracy$ubound,
    icc_results_RT$ubound
  )
)

# Adding ICC Interpretation
icc_data <- icc_data %>%
  mutate(
    Interpretation = case_when(
      ICC < 0.5 ~ "Poor",
      ICC >= 0.5 & ICC < 0.75 ~ "Moderate",
      ICC >= 0.75 & ICC < 0.9 ~ "Good",
      ICC >= 0.9 ~ "Excellent"
    )
  )

# Enhanced plot with custom ICC interpretation in legend
ggplot(icc_data, aes(x = Condition, y = ICC, fill = Condition)) +
  geom_bar(stat = "identity", position = position_dodge(0.7), width = 0.6, color = "black") +
  geom_errorbar(aes(ymin = LowerCI, ymax = UpperCI), width = 0.2, position = position_dodge(0.7)) +
  geom_text(aes(label = Interpretation, y = ICC + 0.05), position = position_dodge(0.7), vjust = -0.5, size = 4) +
  labs(
    title = "ICC Values for Accuracy and Reaction Time (Learning, Control, overall)",
    x = "Condition",
    y = "ICC",
    fill = "Condition"
  ) +
  scale_fill_manual(values = c("Learning" = "#E69F00", "Control" = "#56B4E9" , "overall" = "#009E73")) +
  scale_y_continuous(breaks = seq(0, 1, by = 0.1), limits = c(0, 1)) +
  theme_minimal(base_size = 14) +
  facet_wrap(~ Task, ncol = 2) +
  theme(
    plot.title = element_text(face = "bold", size = 16),
    strip.text = element_text(face = "bold", size = 14),
    legend.position = "bottom",  # Position legend at the bottom for clarity
    legend.text = element_text(size = 10)
  ) +
  # Add an invisible text layer for the custom legend explanation
  annotate("text", x = 2, y = -0.1, label = "ICC Interpretation: Poor (<0.5), Moderate (0.5-0.75), Good (0.75-0.9), Excellent (>0.9)", color = "gray40", size = 4.5, hjust = 0.5)

