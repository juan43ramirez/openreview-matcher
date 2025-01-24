# Measure execution time and print in hours, minutes, and seconds
function print_time {
	local elapsed=$1
	printf "Elapsed time: %02d:%02d:%02d\n" $((elapsed/3600)) $((elapsed%3600/60)) $((elapsed%60))
}

start_time=$SECONDS

# ----------------------------------------------------------------------------------
# Hyper-parameters
# ----------------------------------------------------------------------------------

export DATA_FOLDER="ICML2025/data"
export ASSIGNMENTS_FOLDER="ICML2025/assignments"

export QUANTILE=0.75
export UPWEIGHT_OR_PAPERS=True
export Q=0.5 # Upper bound on the marginal probability of each reviewer-paper pair being matched, for "Randomized" matcher

export OPENREVIEW_USERNAME="your_username"
export OPENREVIEW_PASSWORD="your_password"

# ----------------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------------

# For the matcher
conda create -n openreview-matcher python=3.10
conda activate openreview-matcher
pip install .

# For other scripts
pip install pandas tqdm openreview-py

#
# NOTE: the OR matcher requires a Gurobi license.
#

# Assert all required files exist
# * $DATA_FOLDER/scores_with_origin.csv
# * $DATA_FOLDER/bids.csv
# * $DATA_FOLDER/constraints/conflict_constraints.csv
# * $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv

printf "\nChecking required files..."
for file in $DATA_FOLDER/scores_with_origin.csv $DATA_FOLDER/bids.csv \
	$DATA_FOLDER/constraints/conflict_constraints.csv $DATA_FOLDER/constraints/first_time_reviewer_constraints.csv
do
	if [ ! -f $file ]; then
		printf "File $file does not exist."
		exit 1
	fi
done
print_time $((SECONDS - start_time))
printf "All required files exist."

# Create the output folder
mkdir -p $ASSIGNMENTS_FOLDER


# ----------------------------------------------------------------------------------
# Pre-processing
# ----------------------------------------------------------------------------------

# Aggregate affinity scores
python ICML2025/scripts/aggregate_scores.py \
	--input $DATA_FOLDER/scores_with_origin.csv \
	--output $DATA_FOLDER/aggregated_scores.csv \
	--quantile $QUANTILE \
	--reweight $UPWEIGHT_OR_PAPERS
print_time $((SECONDS - start_time))


# TODO: Filter out suspicious bids

# Translate bids to numeric values
python ICML2025/scripts/translate_bids.py \
	--input $DATA_FOLDER/bids.csv \
	--output $DATA_FOLDER/numeric_bids.csv
print_time $((SECONDS - start_time))

# Filter out bids from reviewers that do not have at least 20 positive bids
python ICML2025/scripts/filter_bids.py \
	--input $DATA_FOLDER/numeric_bids.csv \
	--output $DATA_FOLDER/filtered_bids.csv \
	--min-pos-bids 20
print_time $((SECONDS - start_time))

# ---------------------------------------------------------------------------------
# Initial Matching of 3 reviewers per paper
# ---------------------------------------------------------------------------------

# Join constraints into a single file
python ICML2025/scripts/join_constraints.py \
	--files $DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/first_time_reviewer_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_first_matching.csv
print_time $((SECONDS - start_time))

# Matching
printf "\n----------------------------------------"
printf "\nStarting first matching..."
printf "\n----------------------------------------\n"

python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/filtered_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_first_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 3 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/first_matching.json
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $ASSIGNMENTS_FOLDER/first_matching.csv
print_time $((SECONDS - start_time))

# ---------------------------------------------------------------------------------
# Second matching. Assign a 4th reviewer to each paper
# ---------------------------------------------------------------------------------

# Extract constraints to enforce the previous matching of 3 reviewers per paper on
# the second matching
python ICML2025/scripts/extract_matching_constraints.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.json \
	--output $DATA_FOLDER/constraints/constraints_after_matching.csv
print_time $((SECONDS - start_time))

# Extract geographical diversity constraints
python ICML2025/scripts/geographical_diversity.py \
	--assignments $ASSIGNMENTS_FOLDER/first_matching.csv \
	--output $DATA_FOLDER/constraints/geographical_constraints.csv
print_time $((SECONDS - start_time))

# Join constraints into a single file
python ICML2025/scripts/join_constraints.py \
	--files $DATA_FOLDER/constraints/conflict_constraints.csv \
		$DATA_FOLDER/constraints/constraints_after_matching.csv \
		$DATA_FOLDER/constraints/geographical_constraints.csv \
	--output $DATA_FOLDER/constraints/constraints_for_second_matching.csv
print_time $((SECONDS - start_time))

# Matching
printf "\n----------------------------------------"
printf "\nStarting second matching..."
printf "\n----------------------------------------\n"

python -m matcher \
	--scores $DATA_FOLDER/aggregated_scores.csv $DATA_FOLDER/filtered_bids.csv \
	--weights 1 1 \
	--constraints $DATA_FOLDER/constraints/constraints_for_second_matching.csv \
	--min_papers_default 0 \
	--max_papers_default 6 \
	--num_reviewers 4 \
	--num_alternates 1 \
	--solver Randomized \
	--probability_limits $Q

mv assignments.json $ASSIGNMENTS_FOLDER/second_matching.json
print_time $((SECONDS - start_time))

# Convert assignments JSON to CSV
python ICML2025/scripts/json_to_csv.py \
	--input $ASSIGNMENTS_FOLDER/second_matching.json \
	--output $ASSIGNMENTS_FOLDER/second_matching.csv
print_time $((SECONDS - start_time))

printf "\nDone."