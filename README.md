# Find_ur_restau

# Multi-Criteria Decision Project for Restaurant Selection

This project recommends restaurants based on multiple criteria such as distance, rating, price, pet-friendliness, live music, outdoor seating, vegetarian options, and kids menus. It uses the Google Places API to retrieve restaurant data from various districts of Paris.

## Features

- **API Integration:** Fetches restaurants through the Google Places API.
- **Criteria Normalization:** Normalizes all criteria for fair comparison.
- **User Preferences:** The user sets importance levels for each criterion.
- **Scoring & Ranking:** Calculates a global score for each restaurant and ranks them.
- **Excel Export:** Exports results to `API_Google_Maps.xlsx`.

## Requirements

- Python 3.10+  
  *(If using Python < 3.10, replace `str | None` with `Optional[str]`)*  
- `requests`
- `pandas`
- `openpyxl`
- A valid Google Places API key

## Installation & Usage

1. Clone the repository.
2. Install dependencies (e.g., `conda install requests pandas openpyxl`).
3. Run the script: `python Projet_DMC.py`.
4. Input your preferences when prompted.
5. The top recommended restaurants will be displayed, and the complete list will be saved to an Excel file.

## Customization

- Update criteria and weights directly in the code.
- Modify the `arrondissements` list for different areas.

## License & Disclaimer

- Comply with Google Places API terms.
- Be aware of potential API costs.

## Author

- [Your Name]

## Contributing

- Contributions are welcome. Open issues or submit pull requests for improvements.
