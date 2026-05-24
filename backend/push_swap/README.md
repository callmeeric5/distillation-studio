*This activity has been created as part of the 42 curriculum by ziwang, ildjakov*


# Push_Swap

## Description
This activity will make you sort data on a stack, with a limited set of instructions, using the lowest possible number of actions. To succeed you’ll have to manipulate various types of algorithms and choose the most appropriate solution (out of many) for optimized data sorting. This is a group activity to be completed by exactly 2 learners.

## Website service

The repository root now includes a shared FastAPI service in `api/` and a browser page for running this project as a website feature.

From the repository root:

```
python3 -m venv api/.venv
uv pip install --python api/.venv/bin/python -r api/requirements.txt
api/.venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Open the frontend app and use the Push_swap project page to paste an input, generate a random unique input, choose `simple`, `medium`, or `complex`, then animate the generated operations across stacks A and B.

## Instruction
```
ARG=$(shuf -i 1-500 -n 100); ./push_swap $ARG | ./checker_os $ARG
```

```
shuf -i 0-9999 -n 312 > args.txt && ./push_swap --bench --medium $(cat args.txt) > bench.txt && ./push_swap --medium $(cat args.txt) | ./checker/checker_os $(cat args.txt)
```

## Algorithm

### Simple sort

`simple_sort` is designed for inputs with low disorder (roughly `< 0.2`).
It follows:

1. Find the minimum of stack `a`, based on its position, ra / rra to the top.
2. Push the minimum from `a` to `b`.
3. Continue this process untill only 3 numbers left in stack `a`.
4. Push number from `b` to `a` untill b is empty.

#### Operations Complexity

**The complexity is measured in number of Push_swap operations generated, not the theoretical complexity of a classical array-based algorithm**

- First scan phase (`minimum`): `O(n)`
- Push `a` to `b` & Push `b` to `a`: `O(n^2)`

Total: **`O(n^2)`**

### Medium sort

`complex_sort` is designed for inputs with medium disorder (between `0.2` and `0.5` excluded).
It follows:

1. **Chunk creation**
   - Convert stack `a` into an array and sort it.
   - Divide the sorted values into chunks:
     - 5 chunks for <= 100 elements
     - 11 chunks for > 100 elements
   - Each chunk represents a value range.

2. **Scanning stack A**
   - For the current chunk:
     - Scan from the top → `hold_first`
     - Scan from the bottom → `hold_second`
   - Compute which one is cheaper to bring to the top using `ra` or `rra`.

3. **Move to top**
   - Perform rotations (`ra` or `rra`) to bring the chosen element to the top of stack `a`.

4. **Insert into stack B (ordered insertion)**
   - Before pushing:
     - If the value is greater than max or smaller than min in stack B:
         → rotate B to bring the minimum value to the top
     - Otherwise:
         → find the closest smaller value in B
         → rotate B to place it on top
   - Push with `pb`

5. **Repeat**
   - Repeat steps 2–4 until the current chunk is fully pushed to `b`.
   - Move to the next chunk.

6. **Rebuild stack A**
   - Once all elements are in `b`:
     - Find the **maximum in B**
     - Rotate it to the top
     - Push back to `a` (`pa`)
   - Repeat until `b` is empty.

#### Operations Complexity

**The complexity is measured in number of Push_swap operations generated, not the theoretical complexity of a classical array-based algorithm**

- Chunk creation (array conversion + sorting): `O(n log n)` (preprocessing, not counted in push_swap operations)

- For each element:
  - Scan from top and bottom to find target (`hold_first` / `hold_second`): `O(n)`
  - Rotations in stack `a` to bring the element to top: `O(n)`
  - Rotations in stack `b` to prepare insertion: `O(n)`

- Since elements are processed in chunks of size ≈ `√n`:
  - The number of costly scans and rotations is reduced

Total: **`O(n√n)`**

### Complex Sort

`complex_sort` is designed for inputs with high disorder (roughly `> 0.5`).
It uses a two-phase strategy:

1. Keep an increasing subsequence in stack `a`:
- Scan exactly `size` elements from the top of `a`.
- Track the last accepted index (`last_idx`).
- If `top(a).index > last_idx`, rotate `a` (`ra`) and keep the element in `a`.
- Otherwise, push it to `b` (`pb`) as an out-of-order element.

2. Reinsert out-of-order elements from `b` into `a`:
- While `b` is not empty, evaluate all candidates in `b`.
- For each candidate, compute move costs (combined rotations and single-stack rotations).
- Apply the cheapest move and push back to `a` (`pa`).
- After all insertions, perform a final alignment so the minimum element is at the top.

This keeps most nearly sorted elements in place and only relocates mismatched ones.

#### Operations Complexity

**The complexity is measured in number of Push_swap operations generated, not the theoretical complexity of a classical array-based algorithm**

- First scan phase (`complex_sort` front pass): `O(n)`
- Reinsertion phase (`move_to_a` + `best_move` evaluations): dominant cost, overall `O(nlog(n))`
- Final alignment: `O(n)`

Total: **`O(nlogn)`**

## AI
- Ildjakov : I used AI to ask question about shell commands and for help on my README file
- Ziwang: Gemini for undestanding the subject and the resources, claude for correcting the commands

##  Contributions
**Ildjakov**:
- Medium algorithm
- Disorder function
- Benchmark  option
- Minor changes
- Debugging

**Ziwang**:
- Simple algorithm
- Complex algorithm
- Parser
- Validator
- Debugging

## Resources

- [Push Swap — A journey to find most efficient sorting algorithm](https://medium.com/@ayogun/push-swap-c1f5d2d41e97) by A. Yigit Ogun
- [Push_Swap Turk algorithm explained in 6 steps](https://pure-forest.medium.com/push-swap-turk-algorithm-explained-in-6-steps-4c6650a458c0) by Yutong Deng
- [Push swap visualizer](https://push-swap42-visualizer.vercel.app/) by jel-vous
- [Push_Swap: The least amount of moves with two stacks](https://medium.com/@jamierobertdawson/push-swap-the-least-amount-of-moves-with-two-stacks-d1e76a71789a) by Jamie Dawson
