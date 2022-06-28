from operator import __setitem__
import seaborn as sns
import plotly
import plotly.express as px
from IPython.display import display
from MultiTrain.methods.multitrain_methods import directory, img, img_plotly, kf_best_model, write_to_excel
from skopt import BayesSearchCV
from sklearn.model_selection import train_test_split, KFold, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.model_selection import RandomizedSearchCV, cross_validate
from sklearn.experimental import enable_halving_search_cv # noqa
from sklearn.model_selection import HalvingGridSearchCV, HalvingRandomSearchCV
from sklearnex import patch_sklearn
from sklearnex.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier, PassiveAggressiveClassifier, RidgeClassifier, Perceptron
from sklearn.linear_model import RidgeClassifierCV, LogisticRegressionCV
from sklearnex.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier, HistGradientBoostingClassifier, AdaBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier, BaggingClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB, CategoricalNB, ComplementNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearnex.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.tree import DecisionTreeClassifier, ExtraTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, make_scorer
from sklearn.metrics import mean_absolute_error, r2_score, f1_score, roc_auc_score
from sklearn.metrics import precision_score, recall_score
from MultiTrain.LOGGING.log_message import PrintLog, WarnLog
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import warnings
import time

warnings.filterwarnings("ignore")

patch_sklearn()


class Models:

    def __init__(self, lr=0, lrcv=0, sgdc=0, pagg=0, rfc=0, gbc=0, cat=0, xgb=0, gnb=0, lda=0, knc=0, mlp=0, svc=0,
                 dtc=0, bnb=0, mnb=0, conb=0, hgbc=0, abc=0, etcs=0, rcl=0, rclv=0, etc=0, qda=0,
                 lsvc=0, bc=0, per=0, nu=0) -> None:
        """

        :param lr: Logistic Regression
        :param lrcv: Logistic RegressionCV
        :param sgdc: Stochastic Gradient Descent Classifier
        :param pagg: Passive Aggressive Classifier
        :param rfc: Random Forest Classifier
        :param gbc: Gradient Boosting Classifier
        :param cat: CatBoostClassifier
        :param xgb: XGBoost Classifier
        :param gnb: GaussianNB Classifier
        :param lda: Linear Discriminant Analysis
        :param knc: K Neighbors Classifier
        :param mlp: MLP Classifier
        :param svc: Support Vector Classifier
        :param dtc: Decision Tree Classifier
        :param conb: ComplementNB
        :param hgbc: Hist Gradient Boosting Classifier
        :param abc: Ada Boost Classifier
        :param etcs: Extra Trees Classifier
        :param rcl: Ridge Classifier
        :param rclv: Ridge Classifier CV
        :param etc: Extra Trees Classifier
        :param gpc: Gaussian Process Classifier
        :param qda: Quadratic Discriminant Analysis
        :param lsvc: Linear Support Vector Classifier
        :param bc: Bagging Classifier
        :param per: Perceptron
        :param nu: NuSVC
        """

        self.lr = lr
        self.lrcv = lrcv
        self.sgdc = sgdc
        self.pagg = pagg
        self.rfc = rfc
        self.gbc = gbc
        self.cat = cat
        self.xgb = xgb
        self.gnb = gnb
        self.lda = lda
        self.knc = knc
        self.mlp = mlp
        self.svc = svc
        self.dtc = dtc
        self.bnb = bnb
        self.mnb = mnb
        self.conb = conb
        self.hgbc = hgbc
        self.abc = abc
        self.etcs = etcs
        self.rcl = rcl
        self.rclv = rclv
        self.etc = etc

        self.qda = qda
        self.lsvc = lsvc
        self.bc = bc
        self.per = per
        self.nu = nu
        self.kf_binary_columns = ["Train Acc", "Test Acc", "Train Precision", "Test Precision",
                                  "Train Recall", "Test Recall", "Train f1", "Test f1", 'Train r2',
                                  'Test r2', "Train std", "Test std", "Time Taken(s)"]

        self.kf_multiclass_columns = ["Train Precision Macro", "Test Precision Macro", "Train Recall Macro",
                                      "Test Recall Macro", "Train f1 Macro", "Test f1 Macro", "Time Taken(s)"]

        self.t_split_binary_columns = ["accuracy", "mean absolute error", "mean squared error", "r2 score",
                                       "ROC AUC", "f1 score", "precision", "recall", "execution time(seconds)"]

        self.t_split_multiclass_columns = ["accuracy", "mean absolute error", "mean squared error", "r2 score",
                                           "execution time(seconds)"]


    def split(self,
              X: any,
              y: any,
              strat: bool = False,
              sizeOfTest: float = 0.2,
              randomState: int = None,
              shuffle_data: bool = True):
        """

        :param X: features
        :param y: labels
        :param strat: used to initialize stratify = y in train_test_split if True
        :param sizeOfTest: define size of test data
        :param randomState: define random state
        :param shuffle_data: If set to True, it sets shuffle to True in train_test_split

        Example
        df = pd.read_csv("nameOfFile.csv")
        X = df.drop("nameOfLabelColumn", axis=1)
        y = df["nameOfLabelColumn")
        split(X = features, y = labels, sizeOfTest=0.3, randomState=42, strat=True, shuffle_data=True)
        """
        if isinstance(X, int or bool) or isinstance(y, int or bool):
            raise ValueError(f"{X} and {y} are not valid arguments for 'split'."
                             f"Try using the standard variable names e.g split(X, y) instead of split({X}, {y})")
        elif isinstance(strat, bool) is False:
            raise TypeError("argument of type int or str is not valid. Parameters for strat is either False or True")

        elif sizeOfTest < 0 or sizeOfTest > 1:
            raise ValueError("value of sizeOfTest should be between 0 and 1")

        else:
            if strat is True:

                if shuffle_data is False:
                    raise TypeError("shuffle_data can only be False if strat is False")

                elif shuffle_data is True:
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=sizeOfTest,
                                                                        train_size=1 - sizeOfTest,
                                                                        stratify=y, random_state=randomState,
                                                                        shuffle=shuffle_data)

                    return X_train, X_test, y_train, y_test

            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=sizeOfTest,
                                                                    train_size=1 - sizeOfTest)
                return X_train, X_test, y_train, y_test

    def classifier_model_names(self):
        model_names = ["Logistic Regression", "LogisticRegressionCV", "SGDClassifier", "PassiveAggressiveClassifier",
                       "RandomForestClassifier", "GradientBoostingClassifier", "HistGradientBoostingClassifier",
                       "AdaBoostClassifier", "CatBoostClassifier", "XGBClassifier", "GaussianNB",
                       "LinearDiscriminantAnalysis", "KNeighborsClassifier", "MLPClassifier", "SVC",
                       "DecisionTreeClassifier", "BernoulliNB", "MultinomialNB", "ComplementNB",
                       "ExtraTreesClassifier", "RidgeClassifier", "RidgeClassifierCV", "ExtraTreeClassifier",
                       "QuadraticDiscriminantAnalysis", "LinearSVC", "BaggingClassifier",
                       "Perceptron", "NuSVC"]
        return model_names

    def initialize(self):
        """
        It initializes all the models that we will be using in our ensemble
        """
        self.lr = LogisticRegression(random_state=42, max_iter=1000)
        self.lrcv = LogisticRegressionCV(random_state=42, max_iter=1000, fit_intercept=True)
        self.sgdc = SGDClassifier(random_state=42, early_stopping=True, validation_fraction=0.2,
                                  shuffle=True, n_iter_no_change=20)
        self.pagg = PassiveAggressiveClassifier(shuffle=True, fit_intercept=True, early_stopping=True,
                                                validation_fraction=0.1, n_iter_no_change=20, n_jobs=-1)
        self.rfc = RandomForestClassifier(random_state=42, warm_start=True)
        self.gbc = GradientBoostingClassifier(random_state=42, learning_rate=0.01, validation_fraction=0.1,
                                              n_iter_no_change=20)
        self.hgbc = HistGradientBoostingClassifier(early_stopping=True, validation_fraction=0.2, random_state=42,
                                                   max_iter=300)
        self.abc = AdaBoostClassifier(random_state=42)
        self.cat = CatBoostClassifier(random_state=42, learning_rate=0.01, verbose=False)
        self.xgb = XGBClassifier(use_label_encoder=False, eval_metric="mlogloss")
        self.gnb = GaussianNB()
        self.lda = LinearDiscriminantAnalysis()
        self.knc = KNeighborsClassifier(n_jobs=-1)
        self.mlp = MLPClassifier(batch_size=10, shuffle=True, random_state=42, warm_start=True,
                                 early_stopping=True, n_iter_no_change=20)
        self.svc = SVC(random_state=42)
        self.dtc = DecisionTreeClassifier(random_state=42)
        self.bnb = BernoulliNB()
        self.mnb = MultinomialNB()
        self.conb = ComplementNB()
        self.etcs = ExtraTreesClassifier(warm_start=True, random_state=42, n_jobs=-1)
        self.rcl = RidgeClassifier(random_state=42, max_iter=300)
        self.rclv = RidgeClassifierCV()
        self.etc = ExtraTreeClassifier(random_state=42)
        # self.gpc = GaussianProcessClassifier(warm_start=True, random_state=42, n_jobs=-1)
        self.qda = QuadraticDiscriminantAnalysis()
        self.lsvc = LinearSVC(random_state=42, max_iter=300, fit_intercept=True)
        self.bc = BaggingClassifier(warm_start=True, n_jobs=-1, random_state=42)
        self.per = Perceptron(random_state=42, n_jobs=-1, early_stopping=True, validation_fraction=0.2,
                              n_iter_no_change=20, warm_start=True)
        self.nu = NuSVC(random_state=42)

        return (self.lr, self.lrcv, self.sgdc, self.pagg, self.rfc, self.gbc, self.hgbc, self.abc, self.cat, self.xgb,
                self.gnb, self.lda, self.knc, self.mlp, self.svc, self.dtc, self.bnb, self.mnb, self.conb,
                self.etcs, self.rcl, self.rclv, self.etc, self.qda, self.lsvc, self.bc, self.per, self.nu)

    def _get_index(self, df, the_best):
        name = list(self.classifier_model_names())
        MODEL = self.initialize()
        df['model_names'] = name
        high = ['accuracy', 'f1 score', 'r2 score', 'ROC AUC', 'Test Acc', 'Test Precision',
                'Test Recall', 'Test f1', 'Test r2', 'Test Precision Macro', 'Test Recall Macro',
                'Test f1 Macro']
        low = ['mean absolute error', 'mean squared error', 'Test std']

        if the_best in high:
            best_model_details = df[df[the_best] == df[the_best].max()]

        elif the_best in low:
            best_model_details = df[df[the_best] == df[the_best].min()]

        else:
            raise Exception(f'metric {the_best} not found')

        best_model_details = best_model_details.reset_index()
        best_model_name = best_model_details.iloc[0]['model_names']
        index_ = name.index(best_model_name)
        return MODEL[index_]

    def startKFold(self, param, param_X, param_y, param_cv, fn_target):
        names = self.classifier_model_names()

        if fn_target == 'binary':
            dataframe = {}
            for i in range(len(param)):
                start = time.time()
                score = ('accuracy', 'precision', 'recall', 'f1', 'r2')
                scores = cross_validate(estimator=param[i], X=param_X, y=param_y, scoring=score,
                                        cv=param_cv, n_jobs=-1, return_train_score=True)
                end = time.time()
                seconds = end - start
                mean_train_acc = scores['train_accuracy'].mean()
                mean_test_acc = scores['test_accuracy'].mean()
                mean_train_precision = scores['train_precision'].mean()
                mean_test_precision = scores['test_precision'].mean()
                mean_train_f1 = scores['train_f1'].mean()
                mean_test_f1 = scores['test_f1'].mean()
                mean_train_r2 = scores['train_r2'].mean()
                mean_test_r2 = scores['test_r2'].mean()
                mean_train_recall = scores['train_recall'].mean()
                mean_test_recall = scores['test_recall'].mean()
                train_stdev = scores['train_accuracy'].std()
                test_stdev = scores['test_accuracy'].std()
                # scores = scores.tolist()
                scores_df = [mean_train_acc, mean_test_acc, mean_train_precision, mean_test_precision,
                             mean_train_f1, mean_test_f1, mean_train_r2, mean_test_r2, mean_train_recall,
                             mean_test_recall, train_stdev, test_stdev, seconds]
                dataframe.update({names[i]: scores_df})
            return dataframe

        elif fn_target == 'multiclass':
            dataframe = {}
            for j in range(len(param)):
                start = time.time()
                score = ('precision_macro', 'recall_macro', 'f1_macro')
                scores = cross_validate(estimator=param[j], X=param_X, y=param_y, scoring=score,
                                        cv=param_cv, n_jobs=-1, return_train_score=True)
                end = time.time()
                seconds = end - start
                mean_train_precision = scores['train_precision_macro'].mean()
                mean_test_precision = scores['test_precision_macro'].mean()
                mean_train_f1 = scores['train_f1_macro'].mean()
                mean_test_f1 = scores['test_f1_macro'].mean()
                mean_train_recall = scores['train_recall_macro'].mean()
                mean_test_recall = scores['test_recall_macro'].mean()
                scores_df = [mean_train_precision, mean_test_precision, mean_train_f1, mean_test_f1,
                             mean_train_recall, mean_test_recall, seconds]
                dataframe.update({names[j]: scores_df})
            return dataframe

    def fit(self,
            X: str = None,
            y: str = None,
            split_self: bool = False,
            X_train: str = None,
            X_test: str = None,
            y_train: str = None,
            y_test: str = None,
            split_data: str = None,
            splitting: bool = False,
            kf: bool = False,
            fold: int = 5,
            excel: bool = False,
            return_best_model: str = None,
            return_fastest_model: bool = False,
            target: str = 'binary'
            ):
        """
        If splitting is False, then do nothing. If splitting is True, then assign the values of split_data to the
        variables X_train, X_test, y_train, and y_test

        :param return_fastest_model: defaults to False, set to True when you want the method to only return a dataframe
        of the fastest model

        :param return_best_model: defaults to False, set to True when you want the method to only return a dataframe of
        the best model

        :param split_self: defaults to False, set to True when you split the data yourself

        :param excel: defaults to False, set to True when you want the dataframe to save to an excel file in your
        current working directory

        :param skf: defaults to False, set to True when you want to use StratifiedKFold cross validation as you splitting
        method

        :param y: labels

        :param X: features

        :type fold: object
        :param fold: arguments for KFold where 10 is the n_splits, 1 is the random_state and True is to allow shuffling
        :param kf: defaults to False, set to True when you want to use KFold cross validation as your splitting method
        :param X_train: The training data
        :param X_test: The test data
        :param y_train: The training set labels
        :param y_test: The test set labels
        :param split_data: str = None, splitting: bool = False
        :type split_data: str
        :param splitting: bool = False, defaults to False
        :type splitting: bool (optional)
        :param target: defaults to binary, this is used to specify if the target is binary or multiclass
        If using splitting = True
        df = pd.read_csv("nameOfFile.csv")
        X = df.drop("nameOfLabelColumn", axis=1)
        y = df["nameOfLabelColumn")
        the_split_data = split(X = features, y = labels, sizeOfTest=0.3, randomState=42, strat=True, shuffle_data=True)
        fit_eval_models(splitting = True, split_data = the_split_data)

        If using kf = True

        fit(X = features, y = labels, kf = True, fold = (10, 42, True))
        """

        if isinstance(splitting, bool) is False:
            raise TypeError(
                f"You can only declare object type 'bool' in splitting. Try splitting = False or splitting = True "
                f"instead of splitting = {splitting}")

        if isinstance(kf, bool) is False:
            raise TypeError(
                f"You can only declare object type 'bool' in kf. Try kf = False or kf = True "
                f"instead of kf = {kf}")

        if isinstance(fold, int) is False:
            raise TypeError(
                "param fold is of type int, pass a integer to fold e.g fold = 5, where 5 is number of "
                "splits you want to use for the cross validation procedure")

        if kf:
            if split_self is True:
                raise Exception(
                    "split_self should only be set to True when you split with train_test_split from "
                    "sklearn.model_selection")

            if splitting:
                raise ValueError("KFold cross validation cannot be true if splitting is true and splitting cannot be "
                                 "true if KFold is true")
            """
            if skf:
                raise TypeError("kf cannot be true if skf is true and skf cannot be true if kf is true. You can only "
                                "use one at the same time")
            """
            if split_data:
                raise ValueError("split_data cannot be used with kf, set splitting to True to use param "
                                 "split_data")

        if kf is True and (X is None or y is None or (X is None and y is None)):
            raise ValueError("Set the values of features X and target y")

        if target:
            accepted_targets = ['binary', 'multiclass']
            if target not in accepted_targets:
                raise Exception(f"target should be set to either binary or multiclass but target was set to {target}")

        if splitting is True or split_self is True:
            if splitting and split_data:
                X_tr, X_te, y_tr, y_te = split_data[0], split_data[1], split_data[2], split_data[3]
            elif X_train is not None \
                    and X_test is not None \
                    and y_train is not None \
                    and y_test is not None:
                X_tr, X_te, y_tr, y_te = X_train, X_test, y_train, y_test
            model = self.initialize()
            names = self.classifier_model_names()
            dataframe = {}
            for i in range(len(model)):
                start = time.time()
                try:
                    model[i].fit(X_tr, y_tr)
                except ValueError:
                    pass
                except MemoryError:
                    pass
                end = time.time()
                try:
                    pred = model[i].predict(X_te)
                except AttributeError:
                    pass
                true = y_te

                acc = accuracy_score(true, pred)
                mae = mean_absolute_error(true, pred)
                mse = np.sqrt(mean_absolute_error(true, pred))
                clr = classification_report(true, pred)
                cfm = confusion_matrix(true, pred)
                r2 = r2_score(true, pred)
                try:
                    roc = roc_auc_score(true, pred)
                except ValueError:
                    roc = None
                try:
                    f1 = f1_score(true, pred)
                except ValueError:
                    f1 = None
                try:
                    pre = precision_score(true, pred)
                except ValueError:
                    pre = None
                try:
                    rec = recall_score(true, pred)
                except ValueError:
                    rec = None

                time_taken = round(end - start, 2)
                eval_bin = [acc, mae, mse, r2, roc, f1, pre, rec, time_taken]
                eval_mul = [acc, mae, mse, r2, time_taken]
                if target == 'binary':
                    dataframe.update({names[i]: eval_bin})
                elif target == 'multiclass':
                    dataframe.update({names[i]: eval_mul})

            if target == 'binary':
                df = pd.DataFrame.from_dict(dataframe, orient='index', columns=self.t_split_binary_columns)
            elif target == 'multiclass':
                df = pd.DataFrame.from_dict(dataframe, orient='index', columns=self.t_split_multiclass_columns)

            if return_best_model is not None:
                display(f'BEST MODEL BASED ON {return_best_model}')
                if return_best_model == 'accuracy':
                    display(df[df['accuracy'] == df['accuracy'].max()])
                elif return_best_model == 'mean absolute error':
                    display(df[df['mean absolute error'] == df['mean absolute error'].min()])
                elif return_best_model == 'mean squared error':
                    display(df[df['mean squared error'] == df['mean squared error'].min()])
                elif return_best_model == 'r2 score':
                    display(df[df['r2 score'] == df['r2 score'].max()])
                elif return_best_model == 'f1 score':
                    display(df[df['f1 score'] == df['f1 score'].max()])
                elif return_best_model == 'ROC AUC':
                    display(df[df['ROC AUC'] == df['ROC AUC'].max()])
            elif return_best_model is None:
                display(df.style.highlight_max(color="yellow"))

            if return_fastest_model is True:
                # df.drop(df[df['execution time(seconds)'] == 0.0].index, axis=0, inplace=True)
                display(f"FASTEST MODEL")
                display(df[df["execution time(seconds)"].max()])
            write_to_excel(excel, df)
            print(self.t_split_multiclass_columns)
            return df

        elif kf is True:

            # Fitting the models and predicting the values of the test set.
            KFoldModel = self.initialize()
            names = self.classifier_model_names()

            if target == 'binary':
                PrintLog("Training started")
                dataframe = self.startKFold(param=KFoldModel, param_X=X, param_y=y, param_cv=fold, fn_target=target)

                df = pd.DataFrame.from_dict(dataframe, orient='index', columns=["Train Acc", "Test Acc",
                                                                                "Train Precision", "Test Precision",
                                                                                "Train Recall", "Test Recall",
                                                                                "Train f1", "Test f1", "Train r2",
                                                                                "Test r2",
                                                                                "Train std",
                                                                                "Test std", "Time Taken(s)"])
                kf_ = kf_best_model(df, return_best_model, excel)
                return kf_

            elif target == 'multiclass':
                PrintLog("Training started")
                dataframe = self.startKFold(param=KFoldModel, param_X=X, param_y=y, param_cv=fold, fn_target=target)
                df = pd.DataFrame.from_dict(dataframe, orient='index', columns=["Train Precision Macro",
                                                                                "Test Precision Macro",
                                                                                "Train Recall Macro",
                                                                                "Test Recall Macro",
                                                                                "Train f1 Macro", "Test f1 Macro",
                                                                                "Time Taken(s)"])
                kf_ = kf_best_model(df, return_best_model, excel)
                return kf_

    def use_best_model(self, df, model: str = None, best: str = None):
        """


        :param df: the dataframe object
        :param model: name of the classifier algorithm
        :param best: the evaluation metric used to find the best model

        :return:
        """

        name = self.classifier_model_names()
        MODEL = self.initialize()

        if model is not None and best is not None:
            raise Exception('You can only use one of the two arguments.')

        if model:
            if model not in name:
                raise Exception(f"name {model} is not found, "
                                f"here is a list of the available models to work with: {name}")
            elif model in name:
                index_ = name.index(model)
                return MODEL[index_]

        elif best:
            instance = self._get_index(df, best)
            return instance

    def tune_parameters(self,
                        model: str = None,
                        parameters: dict = None,
                        tune: str = None,
                        use_cpu: int = None,
                        cv: int = 5,
                        n_iter: any = 50,
                        return_train_score: bool = False,
                        refit: bool = True,
                        random_state: int = None,
                        factor: int = 3,
                        verbose: int = 4,
                        resource: any = "n_samples",
                        max_resources: any = "auto",
                        min_resources_grid: any = "exhaust",
                        min_resources_rand: any = "smallest",
                        aggressive_elimination: any = False,
                        error_score: any = np.nan,
                        pre_dispatch: any = "2*n_jobs",
                        optimizer_kwargs: any = None,
                        fit_params: any = None,
                        n_points: any = 1
                        ):
        """
        :param n_points:
        :param fit_params:
        :param optimizer_kwargs:
        :param pre_dispatch:
        :param error_score:
        :param min_resources_grid:
        :param min_resources_rand:
        :param aggressive_elimination:
        :param max_resources:
        :param resource: Defines the resource that increases with each iteration.
        :param verbose:
        :param return_train_score:
        :param refit:
        :param random_state: 
        :param n_iter:
        :param model: This is the instance of the model to be used
        :param factor: To be used with HalvingGridSearchCV, It is the ‘halving’ parameter, which determines the proportion of
        candidates that are selected for each subsequent iteration. For example, factor=3 means that only one third of the
        candidates are selected.
        :param parameters: the dictionary of the model parameters
        :param tune: the type of searching method to use, either grid for GridSearchCV
        or random for RandomSearchCV
        :param use_cpu : the value set determines the number of cores used for training,
        if set to -1 it uses all the available cores
        :param cv:This determines the cross validation splitting strategy, defaults to 5
        :return:
        """
        name = self.classifier_model_names()
        MODEL = self.initialize()
        # index_ = name.index(model)
        # mod = MODEL[index_]

        if isinstance(parameters, dict) is False:
            raise TypeError("The 'parameters' argument only accepts a dictionary of the parameters for the "
                            "model you want to train with.")
        if tune:
            scorers = {
                'precision_score': make_scorer(precision_score),
                'recall_score': make_scorer(recall_score),
                'accuracy_score': make_scorer(accuracy_score)
            }

            if tune == 'grid':
                tuned_model = GridSearchCV(estimator=model, param_grid=parameters, n_jobs=use_cpu, cv=cv,
                                           verbose=verbose, error_score=error_score, pre_dispatch=pre_dispatch,
                                           return_train_score=return_train_score, scoring=scorers, refit=refit)
                return tuned_model

            elif tune == 'random':
                tuned_model = RandomizedSearchCV(estimator=model, param_distributions=parameters, n_jobs=use_cpu, cv=cv,
                                                 verbose=verbose, random_state=random_state, n_iter=n_iter,
                                                 return_train_score=return_train_score, error_score=error_score,
                                                 scoring=scorers, refit=refit, pre_dispatch=pre_dispatch)
                return tuned_model

            elif tune == 'bayes':
                tuned_model = BayesSearchCV(estimator=model, search_spaces=parameters, n_jobs=use_cpu,
                                            return_train_score=return_train_score, cv=cv, verbose=verbose,
                                            refit=refit, random_state=random_state, scoring=scorers,
                                            error_score=error_score, optimizer_kwargs=optimizer_kwargs,
                                            n_points=n_points, n_iter=n_iter, fit_params=fit_params,
                                            pre_dispatch=pre_dispatch)
                return tuned_model

            elif tune == 'half-grid':
                tuned_model = HalvingGridSearchCV(estimator=model, param_grid=parameters, n_jobs=use_cpu, cv=cv,
                                                  verbose=4, random_state=42, factor=factor, refit=refit,
                                                  scoring=scorers, resource=resource, min_resources=min_resources_grid,
                                                  max_resources=max_resources, error_score=error_score,
                                                  aggressive_elimination=aggressive_elimination)

                return tuned_model

            elif tune == 'half-random':
                tuned_model = HalvingRandomSearchCV(estimator=model, param_distributions=parameters, n_jobs=use_cpu,
                                                    cv=cv, verbose=4, random_state=42, factor=factor, refit=refit,
                                                    scoring=scorers, resource=resource, error_score=error_score,
                                                    min_resources=min_resources_rand, max_resources=max_resources,
                                                    aggressive_elimination=aggressive_elimination)
                return tuned_model

    def visualize(self,
                  param: {__setitem__},
                  file_path: any = None,
                  kf: bool = False,
                  t_split: bool = False,
                  size=(15, 8),
                  save: str = None,
                  save_name='dir1',
                  ):

        """
        The function takes in a dictionary of the model names and their scores, and plots them in a bar chart

        :param file_path:
        :param param: {__setitem__}
        :type param: {__setitem__}
        :param kf: set to True if you used KFold, defaults to False
        :type kf: bool (optional)
        :param t_split: True if you used the split method, defaults to False
        :type t_split: bool (optional)
        :param size: This is the size of the plot
        :param save: This is the format you want to save the plot in
        :type save: str
        :param save_name: The name of the file you want to save the visualization as, defaults to dir1 (optional)
        """

        names = self.classifier_model_names()
        sns.set()

        param['model_names'] = names
        FILE_FORMATS = ['pdf', 'png']
        if save not in FILE_FORMATS:
            raise Exception("set save to either 'pdf' or 'png' ")

        if save in FILE_FORMATS:
            if isinstance(save_name, str) is False:
                raise ValueError('You can only set a string to save_name')

            if save_name is None:
                raise Exception('Please set a value to save_name')

        if file_path:
            if save is None:
                raise Exception("set save to either 'pdf' or 'png' before defining a file path")

        if save is None:
            if save_name:
                raise Exception('You can only use save_name after param save is defined')

        if kf is True and t_split is True:
            raise Exception("set kf to True if you used KFold or set t_split to True"
                            "if you used the split method.")
        if kf is True:

            plt.figure(figsize=size)
            plot = sns.barplot(x="model_names", y="mean score", data=param)
            plot.set_xticklabels(plot.get_xticklabels(), rotation=90)
            plt.title("MEAN SCORE")

            plt.figure(figsize=size)
            plot1 = sns.barplot(x="model_names", y="std", data=param)
            plot1.set_xticklabels(plot1.get_xticklabels(), rotation=90)
            plt.title("STANDARD DEVIATION")

            if save == 'pdf':
                name = save_name + ".pdf"
                img(name, FILE_PATH=file_path, type_='file')

            elif save == 'png':
                name = save_name
                img(FILENAME=name, FILE_PATH=file_path, type_='picture')

            display(plot)
            display(plot1)

        elif t_split is True:

            plt.figure(figsize=size)
            plot = sns.barplot(x="model_names", y="accuracy", data=param)
            plot.set_xticklabels(plot.get_xticklabels(), rotation=90)
            plt.title("ACCURACY")

            plt.figure(figsize=size)
            plot1 = sns.barplot(x="model_names", y="mean absolute error", data=param)
            plot1.set_xticklabels(plot1.get_xticklabels(), rotation=90)
            plt.title("MEAN ABSOLUTE ERROR")

            plt.figure(figsize=size)
            plot2 = sns.barplot(x="model_names", y="mean squared error", data=param)
            plot2.set_xticklabels(plot2.get_xticklabels(), rotation=90)
            plt.title("MEAN SQUARED ERROR")

            plt.figure(figsize=size)
            plot3 = sns.barplot(x="model_names", y="r2 score", data=param)
            plot3.set_xticklabels(plot3.get_xticklabels(), rotation=90)
            plt.title("R2 SCORE")

            try:
                plt.figure(figsize=size)
                plot4 = sns.barplot(x="model_names", y="ROC AUC", data=param)
                plot4.set_xticklabels(plot4.get_xticklabels(), rotation=90)
                plt.title("ROC AUC")
            except None in param["ROC AUC"]:
                plot4 = 'ROC AUC cannot be visualized'

            try:
                plt.figure(figsize=size)
                plot5 = sns.barplot(x="model_names", y="f1 score", data=param)
                plot5.set_xticklabels(plot5.get_xticklabels(), rotation=90)
                plt.title("F1 SCORE")
            except None in param["f1 score"]:
                plot5 = 'f1 score cannot be visualized'

            if save == 'pdf':
                name = save_name + ".pdf"
                img(name, FILE_PATH=file_path, type_='file')
            elif save == 'png':
                name = save_name
                img(FILENAME=name, FILE_PATH=file_path, type_='picture')

            display(plot)
            display(plot1)
            display(plot2)
            display(plot3)
            display(plot4)
            display(plot5)

    def show(self,
             param: {__setitem__},
             file_path: any = None,
             kf: bool = False,
             t_split: bool = False,
             save: bool = False,
             save_name=None,
             target='binary',
             ):
        """
                The function takes in a dictionary of the model names and their scores, and plots them in a bar chart

                :param target:
                :param file_path:
                :param param: {__setitem__}
                :type param: {__setitem__}
                :param kf: set to True if you used KFold, defaults to False
                :type kf: bool (optional)
                :param t_split: True if you used the split method, defaults to False
                :type t_split: bool (optional)
                :param size: This is the size of the plot
                :param save_name: The name of the file you want to save the visualization as.
                """

        names = self.classifier_model_names()

        param['model_names'] = names

        if kf is True:
            if t_split is True:
                raise Exception("set kf to True if you used KFold or set t_split to True"
                                "if you used the split method.")
            if target == 'binary':
                IMAGE_COLUMNS = []
                for i in range(len(self.kf_binary_columns)):
                    IMAGE_COLUMNS.append(self.kf_binary_columns[i] + ".png")

                if save is True:
                    dir = directory(save_name)
                for j in range(len(IMAGE_COLUMNS)):

                    fig = px.bar(data_frame=param,
                                 x="model_names",
                                 y=self.kf_binary_columns[j],
                                 hover_data=[self.kf_binary_columns[j], "model_names"],
                                 color="Time Taken(s)")
                    display(fig)
                    if save is True:
                        if save_name is None:
                            raise Exception("set save to True before using save_name")

                        else:
                            img_plotly(
                                name=IMAGE_COLUMNS[j],
                                figure=fig,
                                label=target,
                                FILENAME=dir,
                                FILE_PATH=file_path,
                            )

            elif target == 'multiclass':
                IMAGE_COLUMNS = []
                for i in range(len(self.kf_multiclass_columns)):
                    IMAGE_COLUMNS.append(self.kf_multiclass_columns[i] + ".png")

                if save is True:
                    dir = directory(save_name)

                for j in range(len(self.kf_multiclass_columns)):
                    fig = px.bar(data_frame=param,
                                 x="model_names",
                                 y=self.kf_multiclass_columns[j],
                                 hover_data=[self.kf_multiclass_columns[j], "model_names"],
                                 color="Time Taken(s)")
                    display(fig)
                    if save is True:
                        if save_name is None:
                            raise Exception("set save to True before using save_name")

                        elif save_name:
                            img_plotly(
                                name=IMAGE_COLUMNS[j],
                                figure=fig,
                                label=target,
                                FILENAME=dir,
                                FILE_PATH=file_path,
                            )

        if t_split is True:
            if kf is True:
                raise Exception("set kf to True if you used KFold or set t_split to True"
                                "if you used the split method.")

            if target == 'binary':
                IMAGE_COLUMNS = []
                for i in range(len(self.t_split_binary_columns)):
                    IMAGE_COLUMNS.append(self.t_split_binary_columns[i] + ".png")

                if save is True:
                    dir = directory(save_name)
                for j in range(len(IMAGE_COLUMNS)):

                    fig = px.bar(data_frame=param,
                                 x="model_names",
                                 y=self.t_split_binary_columns[j],
                                 hover_data=[self.t_split_binary_columns[j], "model_names"],
                                 color="execution time(seconds)")
                    display(fig)
                    if save is True:
                        if save_name is None:
                            raise Exception("set save to True before using save_name")

                        else:
                            img_plotly(
                                name=IMAGE_COLUMNS[j],
                                figure=fig,
                                label=target,
                                FILENAME=dir,
                                FILE_PATH=file_path,
                            )

            elif target == 'multiclass':
                IMAGE_COLUMNS = []
                for i in range(len(self.t_split_multiclass_columns)):
                    IMAGE_COLUMNS.append(self.t_split_multiclass_columns[i] + ".png")

                if save is True:
                    dir = directory(save_name)

                for j in range(len(self.t_split_multiclass_columns)):
                    fig = px.bar(data_frame=param,
                                 x="model_names",
                                 y=self.t_split_multiclass_columns[j],
                                 hover_data=[self.t_split_multiclass_columns[j], "model_names"],
                                 color="execution time(seconds)")
                    display(fig)
                    if save is True:
                        if save_name is None:
                            raise Exception("set save to True before using save_name")

                        elif save_name:
                            img_plotly(
                                name=IMAGE_COLUMNS[j],
                                figure=fig,
                                label=target,
                                FILENAME=dir,
                                FILE_PATH=file_path,
                            )
