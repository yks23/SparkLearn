import logging
import json
import os
import asyncio
from src.utils.id_operation import realloc_id


class ProcessManager:
    def __init__(
        self, workflow: list[str] = None, state_path: str = None, from_scratch: bool = True
    ):
        if workflow is None:
            workflow = [
            "doc2section",
            "community_report",
            "section2tree",
            "augmentent",
            "augmentrel",
            "aggregation-naive",
            "identical_predict",
            "connection_predict",
            "continue_iteration",
        ]
        self.workflow = workflow
        self.processed = 0
        if state_path == None:
            from src.config import metadata_path

            self.state_path = os.path.join(metadata_path, "state.json")
        else:
            self.state_path = state_path
        if not from_scratch:
            self.load_state()

    @staticmethod
    def get_default_manager():
        workflow = [
            "doc2section",
            "community_report",
            "section2tree",
            "augmentent",
            "augmentrel",
            "aggregation-naive",
            # "aggregation-llm",
            "identical_predict",
            "connection_predict",
            "continue_iteration",
        ]
        return ProcessManager(workflow)

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.workflow = state["workflow"]
                self.processed = state["processed"]

    def save_state(self):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    def to_dict(self):
        return {"workflow": self.workflow, "processed": self.processed}

    def step(self):
        from src.config import metadata_path

        onprocess_task = self.workflow[self.processed]
        print("onprocess_task", onprocess_task)
        if onprocess_task == "doc2section":
            from src.workflow.initial_skeleton.documents_to_section import (
                documents_to_sections,
            )

            documents_to_sections()
            realloc_id()
            self.processed += 1
        elif onprocess_task == "community_report":
            from src.workflow.initial_skeleton.community_report import community_report

            community_report()
            realloc_id()
            self.processed += 1
        elif onprocess_task == "section2tree":
            from src.workflow.initial_skeleton.entity_extraction import (
                entity_extraction,
            )

            entity_extraction()
            realloc_id()
            self.processed += 1
        elif onprocess_task == "augmentent":
            from src.workflow.augmentation.augmented_generation import (
                augmented_generation,
            )

            if not "augmentent" in self.workflow[: self.processed]:
                augmented_generation(True, False, True)
            else:
                augmented_generation(True, False, False)
            self.processed += 1
        elif onprocess_task == "augmentrel":
            from src.workflow.augmentation.augmented_generation import (
                augmented_generation,
            )

            if not "augmentent" in self.workflow[: self.processed]:
                augmented_generation(False, True, True)
            else:
                augmented_generation(False, True, False)
        elif onprocess_task == "aggregation-naive":
            from src.workflow.augmentation.transportation import get_local_role

            get_local_role(need_ask=False)
            self.processed += 1
        elif onprocess_task == "aggregation-llm":
            get_local_role(need_ask=True)
            self.processed += 1
        elif onprocess_task == "identical_predict":
            from src.workflow.augmentation.relation_predict import identical_predict

            identical_predict(
                0.55,
                engine_path=os.path.join(metadata_path, "engine.ann"),
                table_path=os.path.join(metadata_path, "table.json"),
                folder_path=metadata_path,
            )
            self.processed += 1
        elif onprocess_task == "connection_predict":
            from src.workflow.augmentation.relation_predict import connection_predict

            connection_predict(5)
            self.processed += 1
        elif onprocess_task == "continue_iteration":
            from src.workflow.augmentation.relation_predict import continue_predict

            continue_predict()
            self.processed += 1
        elif onprocess_task_name == "visualization_internal":
            from src.workflow.visualization.tree_visualize import tree_visualization

            asyncio.run(tree_visualization())

            self.processed += 1
        elif isinstance(onprocess_task, dict):
            onprocess_task_name = onprocess_task["name"]
            if onprocess_task_name == "internal2uniform":
                from src.eval.prepare_for_eval import internal2uniform

                data_root = onprocess_task.get("data_root", metadata_path)
                internal2uniform(data_root)
                self.processed += 1
            elif onprocess_task_name == "eval_ES":
                from src.eval.eval_entity import ES_external

                if "target_field" in onprocess_task.keys():
                    target_field = onprocess_task["target_field"]
                if "data_root" in onprocess_task.keys():
                    data_path = onprocess_task["data_root"]
                else:
                    data_path = os.path.join(metadata_path, "eval")
                ES_external(target_field, data_path)
                self.processed += 1
            elif onprocess_task_name == "eval_RS":
                from src.eval.eval_relation import RS_external

                if "data_root" in onprocess_task.keys():
                    data_path = onprocess_task["data_root"]
                else:
                    data_path = os.path.join(metadata_path, "eval")
                # print("data_path", data_path)
                RS_external(data_path)
                self.processed += 1
            elif onprocess_task_name == "eval_ER":
                gt_root = onprocess_task["gt_root"]
                pred_root = onprocess_task["pred_root"]
                from src.eval.eval_entity import ER_CROSS

                ER_CROSS(gt_root, pred_root)
                self.processed += 1
            elif onprocess_task_name == "external2uniform":
                data_root = onprocess_task["data_root"]
                from src.eval.prepare_for_eval import external2uniform

                external2uniform(data_root)
                self.processed += 1
            elif onprocess_task_name == "MEC&MED":
                gt_root = onprocess_task["gt_root"]
                pred_root = onprocess_task["pred_root"]
                from src.eval.eval_mapping import MEC_MED

                MEC_MED(gt_root, pred_root)
                self.processed += 1
            elif onprocess_task_name == "visualization_external":
                from src.workflow.visualization.visual_others import (
                    visualize_native_graph,
                )

                data_root = onprocess_task.get("data_root", metadata_path)
                asyncio.run(visualize_native_graph(data_root))
                self.processed += 1

    def execute(self):
        for i, task in enumerate(self.workflow):
            print(f"{i+1}: {task}")
        while self.processed < len(self.workflow):
            logging.info(
                f"================Processed {self.processed}/{len(self.workflow)}================="
            )
            self.step()
            self.save_state()
        print("All tasks completed.")
