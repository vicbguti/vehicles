from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    encode_features,
    report_confusion_matrices,
    split_data,
    train_attention,
    train_lightgbm,
    train_xgboost,
)


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=encode_features,
                inputs=["vehicles", "episodes"],
                outputs="encoded_vehicles",
                name="encode",
            ),
            node(
                func=split_data,
                inputs=["encoded_vehicles", "params:split"],
                outputs=["train_df", "val_df"],
                name="split",
            ),
            node(
                func=train_xgboost,
                inputs=[
                    "train_df",
                    "val_df",
                    "episodes",
                    "params:xgboost.max_depth",
                    "params:xgboost.learning_rate",
                    "params:xgboost.n_estimators",
                    "params:xgboost.subsample",
                    "params:xgboost.colsample_bytree",
                    "params:xgboost.min_child_weight",
                    "params:xgboost.scale_pos_weight",
                    "params:xgboost.max_delta_step",
                    "params:xgboost.run_name",
                ],
                outputs={"xgb_results": "xgb_results", "xgb_predictions": "xgb_predictions"},
                name="train_xgboost",
            ),
            node(
                func=train_lightgbm,
                inputs=[
                    "train_df",
                    "val_df",
                    "episodes",
                    "params:lightgbm.num_leaves",
                    "params:lightgbm.learning_rate",
                    "params:lightgbm.n_estimators",
                    "params:lightgbm.subsample",
                    "params:lightgbm.colsample_bytree",
                    "params:lightgbm.min_child_samples",
                    "params:lightgbm.scale_pos_weight",
                    "params:lightgbm.run_name",
                ],
                outputs={"lgb_results": "lgb_results", "lgb_predictions": "lgb_predictions"},
                name="train_lightgbm",
            ),
            node(
                func=train_attention,
                inputs=[
                    "train_df",
                    "val_df",
                    "episodes",
                    "params:attention.d_model",
                    "params:attention.nhead",
                    "params:attention.num_layers",
                    "params:attention.dropout",
                    "params:attention.batch_size",
                    "params:attention.learning_rate",
                    "params:attention.n_epochs",
                    "params:attention.run_name",
                ],
                outputs={"att_results": "att_results", "att_predictions": "att_predictions"},
                name="train_attention",
            ),
            node(
                func=report_confusion_matrices,
                inputs=[
                    "xgb_predictions",
                    "lgb_predictions",
                    "att_predictions",
                    "xgb_results",
                    "lgb_results",
                ],
                outputs={
                    "xgb_confusion_matrix_train": "xgb_confusion_matrix_train",
                    "xgb_confusion_matrix_val": "xgb_confusion_matrix_val",
                    "lgb_confusion_matrix_train": "lgb_confusion_matrix_train",
                    "lgb_confusion_matrix_val": "lgb_confusion_matrix_val",
                    "att_confusion_matrix_val": "att_confusion_matrix_val",
                },
                name="report_confusion_matrices",
            ),
        ]
    )
