# run via python3 -m app.tests.test

from app.services.grammar_service import chunk_sentences


text = """Last weekend, I went to the park with my friends. We was very excited to spend time together because it was a sunny day. When we arrived, we first went to the cafe to buy some drink. I ordered a coffee and my friend Maria, she ordered a tea. We was talking about the new movie that just came out, and we decide to watch it later in the evening. It’s a comedy film, so we was hoping it would make us laugh a lot.

After we finish our drinks, we walked around the park. The park was really beautiful, with flowers everywhere. We seen some children playing on the swings and their parents were sitting on the bench, watching them. The birds were singing loud and there was a nice breeze that make the trees move. It’s the perfect day for outdoor activities, I think.

Later, we decided to play frisbee. We don’t play it often, but it’s always fun. We didn’t have a lot of energy, so we only play for a little while before we went to sit down again. While sitting, we talked about plans for the future. I says that I want to travel to different countries and see new places. Maria said she want to learn how to cook better, and John says he’s thinking about moving to another city for work.

We was all really enjoying the time together. Sometimes, I feel that people don’t appreciate the small moments like these. It’s easy to get caught up in our busy lives and forget how important it is to relax with friends. That’s why I think we should do things like this more often.

Before we leave the park, we took some pictures. I didn’t bring my camera, so I used my phone. The pictures was nice, and I am planning to show them to my family. It’s always good to have memories from fun times. We said goodbye and promised to meet again soon. On the way back, we talked about how fun the day was, and how we can’t wait to do it again.

The only bad thing about the day was that I forgot my wallet at home, so I couldn’t pay for the drinks. Thankfully, Maria paid for me. I feel bad for that, but she said it’s okay. Next time, I will remember to bring my wallet with me."""

chunks = chunk_sentences(text)
for chunk in chunks:
    print(chunk)
