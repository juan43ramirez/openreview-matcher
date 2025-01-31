#conda create -n secure-paper-bidding python=3.10
#conda activate secure-paper-bidding
#pip install ortools scipy torch numpy tqdm openreview-py

cd ICML2025/secure-paper-bidding
bash scripts/init_and_data_process_script.sh
bash scripts/assignment_script.sh # train model
bash scripts/detect_tpr_script.sh # evaluate collusion
