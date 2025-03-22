import unittest
import numpy as np
from parameterized import parameterized
from sklearn.datasets import load_breast_cancer, load_diabetes
from flexml.logger import get_logger
from flexml import Regression, Classification

import warnings
warnings.filterwarnings("ignore")

class TestCrossValidation(unittest.TestCase):
    logger = get_logger(__name__, "TEST", logging_to_file=False)

    # Datasets for testing
    regression_data = load_diabetes(as_frame=True)['frame']
    breast_data = load_breast_cancer(as_frame=True)
    classification_data = breast_data['frame']
    classification_data["target"] = breast_data['target']
    classification_data["group"] = classification_data.index % 3  # Add synthetic group column
    regression_data["group"] = regression_data.index % 3  # Add synthetic group column

    @parameterized.expand([
        ("Classification", "kfold", {"n_splits": 3}),
        ("Classification", "stratified_kfold", {"n_splits": 3}),
        ("Classification", "shuffle_split", {"n_splits": 3, "test_size": 0.25}),
        ("Classification", "stratified_shuffle_split", {"n_splits": 3, "test_size": 0.25}),
        ("Classification", "group_kfold", {"n_splits": 3, "groups_col": "group"}),
        ("Classification", "group_shuffle_split", {"n_splits": 3, "test_size": 0.25, "groups_col": "group"}),
        ("Classification", "holdout", {"test_size": 0.25}),
        ("Regression", "kfold", {"n_splits": 3}),
        ("Regression", "shuffle_split", {"n_splits": 3, "test_size": 0.25}),
        ("Regression", "group_kfold", {"n_splits": 3, "groups_col": "group"}),
        ("Regression", "group_shuffle_split", {"n_splits": 3, "test_size": 0.2, "groups_col": "group"}),
        ("Regression", "holdout", {"test_size": 0.25}),
    ])
    def test_cross_validation(
        self,
        ml_task_type: str,
        cv_method: str,
        params: dict
    ):
        target_col = "target"

        if ml_task_type == "Classification":
            df = self.classification_data.copy()

            # Skip Stratified methods if classes are not sufficiently populated
            has_sufficient_class_instances = not ("Stratified" in cv_method and (df["target"].value_counts() < 2).any())
            self.assertTrue(
                has_sufficient_class_instances, 
                f"{cv_method} couldn't be executed due to insufficient class instances, please take a look to data used for the test"
            )

            experiment_object = Classification(df, target_col)
            
        else: # Classification
            self.assertNotIn(
                "Stratified",
                cv_method, 
                f"Stratified methods are for Classification only. You've passed {cv_method} for Regression"
            )

            df = self.regression_data.copy()
            experiment_object = Regression(df, target_col)
        
        experiment_object.start_experiment(
            experiment_size="wide",
            cv_method=cv_method,
            n_folds=params.get("n_splits"),
            test_size=params.get("test_size"),
            groups_col=params.get("groups_col")
        )

        predictions = experiment_object.predict(df.drop(columns=[target_col]), full_train=False)
        self.assertIsInstance(predictions, np.ndarray)