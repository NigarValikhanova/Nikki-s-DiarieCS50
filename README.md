# NikkiDiarieCS50

<h3> Video Demo: https://www.youtube.com/watch?v=rCAk_v6R4Wc </h3>

This is the final project for CS50x, created by **Nigar Valikhanova**. NikkiDiarieCS50 is a personal diary web application where users can register, log in, and create, view, edit, and delete their diary entries. The app features multiple pages including a calendar view, a gallery, and an about section. The application is built using Python (Flask), JavaScript, and SQL, integrating user authentication and profile management.

## Features

- **User Authentication:** Secure registration and login functionality with form validation.
- **Diary Management:** Users can create, edit, and delete personal diary entries.
- **Profile Customization:** Users can update their profile picture and edit profile information.
- **Calendar Integration:** View diary entries organized by date.
- **Gallery:** Display images that users upload to their diary.
- **Multilingual Support:** Language options for a personalized user experience.
- **Responsive Design:** The web app is fully responsive and designed to look good on both mobile and desktop.

## Pages

1. **Home:** Introduction and overview of the app.
2. **Register/Login:** Users can sign up or log in with an existing account.
3. **Diary Entries:** View, add, edit, or delete personal diary entries.
4. **Profile:** Update user profile and upload profile picture.
5. **Calendar:** Visualize entries by date on a calendar.
6. **Gallery:** A page where users can view and manage uploaded images.
7. **About:** Information about the creator and the application.

## Technologies Used

- **Backend:** Python with Flask framework
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Database:** SQLite for storing user information and diary entries
- **Other Libraries:**
  - Flask-WTF for form handling
  - Flask-Login for user authentication
  - SQLAlchemy for database management
  - jQuery and Bootstrap for responsive design and UI interaction

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NigarValikhanova/NikkiDiarieCS50.git
   cd NikkiDiarieCS50
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. Run the application:
   ```bash
   flask run
   ```

## Usage

- **Register** a new account, or **log in** with an existing account.
- Create, edit, or delete diary entries from the **Diary Entries** page.
- Update your profile picture and personal information in the **Profile** section.
- View your diary entries organized by date on the **Calendar** page.
- Upload and view your images in the **Gallery**.

## License

This project is licensed under the MIT License.
