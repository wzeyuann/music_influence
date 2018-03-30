data = read.csv('true_pred_by_year.csv')
logit = glm(correct_pred ~ years_between, data=data, family='binomial')
logit.int = glm(correct_pred ~ 1, data=data, family='binomial')
summary(logit)

# Perform likelihood ratio test
anova(logit, logit.int, test='Chisq')
