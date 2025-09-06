package com.mohit.emailorganizer;

import jakarta.mail.*;
import jakarta.mail.internet.MimeMessage;
import java.util.Properties;

public class EmailFetcher {

    public static void fetchUnreadEmails(String username, String password) {
        Properties props = new Properties();
        props.put("mail.store.protocol", "imaps");

        try {
            Session session = Session.getDefaultInstance(props, null);
            Store store = session.getStore("imaps");
            store.connect("imap.gmail.com", username, password);

            Folder inbox = store.getFolder("INBOX");
            inbox.open(Folder.READ_ONLY);

            Message[] messages = inbox.search(new FlagTerm(new Flags(Flags.Flag.SEEN), false));

            System.out.println("Unread emails: " + messages.length);
            for (Message message : messages) {
                System.out.println("From: " + message.getFrom()[0]);
                System.out.println("Subject: " + message.getSubject());
                System.out.println("------------");
            }

            inbox.close(false);
            store.close();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
