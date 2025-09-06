package com.mohit.emailorganizer;

public class Main {
    public static void main(String[] args) {
        String email = "your-email@gmail.com";
        String appPassword = "your-app-password"; // Use Gmail App Password, not your actual password
        EmailFetcher.fetchUnreadEmails(email, appPassword);
    }
}
