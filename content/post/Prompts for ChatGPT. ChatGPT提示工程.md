+++
date = "2023-06-19"
title = "Prompts for ChatGPT. ChatGPT提示工程"
slug = "prompts-for-chatgpt"
categories = [ "AI", "工具" ]
tags = [ "ChatGPT", "提示工程", "Prompt" ]
readingtime = true
+++

**目录**

*   [润色](#%E6%B6%A6%E8%89%B2)
*   [纠正语法](#%E7%BA%A0%E6%AD%A3%E8%AF%AD%E6%B3%95)
*   [精减语句](#%E7%B2%BE%E5%87%8F%E8%AF%AD%E5%8F%A5)
*   [扩充语句](#%E6%89%A9%E5%85%85%E8%AF%AD%E5%8F%A5)
*   [改变语气](#%E6%94%B9%E5%8F%98%E8%AF%AD%E6%B0%94)
    *   [专业化](#%E4%B8%93%E4%B8%9A%E5%8C%96)
    *   [日常化](#%E6%97%A5%E5%B8%B8%E5%8C%96)
    *   [直率化](#%E7%9B%B4%E7%8E%87%E5%8C%96)
    *   [自信化](#%E8%87%AA%E4%BF%A1%E5%8C%96)
    *   [友好化](#%E5%8F%8B%E5%A5%BD%E5%8C%96)
*   [简化语句](#%E7%AE%80%E5%8C%96%E8%AF%AD%E5%8F%A5)
*   [改写语句](#%E6%94%B9%E5%86%99%E8%AF%AD%E5%8F%A5)
*   [概括内容](#%E6%A6%82%E6%8B%AC%E5%86%85%E5%AE%B9)
*   [分析关键要点](#%E5%88%86%E6%9E%90%E5%85%B3%E9%94%AE%E8%A6%81%E7%82%B9)
*   [翻译语句](#%E7%BF%BB%E8%AF%91%E8%AF%AD%E5%8F%A5)
*   [解释内容](#%E8%A7%A3%E9%87%8A%E5%86%85%E5%AE%B9)
*   [列举我们该朝什么方向行动](#%E5%88%97%E4%B8%BE%E6%88%91%E4%BB%AC%E8%AF%A5%E6%9C%9D%E4%BB%80%E4%B9%88%E6%96%B9%E5%90%91%E8%A1%8C%E5%8A%A8)

使用`{{ }}`包裹的内容需要根据自己的需求进行替换，如我想要润色以下句子并让ChatGPT输出英文： `今天天气很好` 你需要向ChatGPT输入：

    I will give you text content, you will rewrite it and output a better version of my text.
    
    Keep the meaning the same. Make sure the re-written content's number of characters is the same as the original text's number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.
    
    Now, using the concepts above, re-write the following text. Respond in English:
    
    """
    今天天气很好
    """
    

润色
--

I will give you text content, you will rewrite it and output a better version of my text.

Keep the meaning the same. Make sure the re-written content’s number of characters is the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

纠正语法
----

I will give you text content, you will correct the spelling, syntax and grammar of this text. Correct any spelling, syntax, or grammar mistakes in the text I give you without making any improvements or changes to the original meaning or style. In other words, only correct spelling, syntax, or grammar mistakes, do not make improvements. If the original text has no mistake, just output the original text and nothing else.

Keep the meaning the same. Make sure the re-written content’s number of words is the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

精减语句
----

I’ll give you text. You’ll rewrite it and output it shorter to be no more than half the number of characters of the original text.

Keep the meaning the same. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

扩充语句
----

I’ll give you text. You’ll rewrite it and output it longer to be more than twice the number of characters of the original text.

Keep the meaning the same. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

改变语气
----

专业化
---

Definition of “professional tone”: “A professional tone is a way of writing that conveys a sense of formality, respect, and competence. A person writing with a professional tone uses language and intonation that is more formal and appropriate for a business or formal setting. A professional tone can be identified by a number of verbal and nonverbal cues, including:

*   Use of formal language and vocabulary
*   Avoidance of slang and colloquial expressions
*   Appropriate use of titles and honorifics
*   Direct and concise statements
*   Maintaining a neutral tone
*   Use of polite language and manners

Overall, a professional tone communicates a sense of competence and credibility, which can help establish trust and influence in business or formal settings. It is important to note that a professional tone should be tailored to the specific situation and audience, as different contexts may require different levels of formality or informality.”

I will give you text content, you will rewrite it and output that in a “professional tone”.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

日常化
---

Definition of “casual tone”: “A casual tone is a way of writing that conveys informality, relaxation, and a sense of ease. A person writing with a casual tone uses language and intonation that is less formal and more relaxed, conveying a sense of familiarity and comfort. A casual tone can be identified by a number of verbal and nonverbal cues, including:

*   Use of informal language and slang
*   Use of contractions
*   Use of humor and anecdotes
*   Intonation and tone that is less formal

Overall, a casual tone communicates a sense of informality and friendliness, which can help establish a more relaxed and comfortable atmosphere in both personal and professional contexts. It is important to note that while a casual tone can be appropriate in some situations, it may not be suitable for all situations and should be used with discretion.”

I will give you text content, you will rewrite it and output that in a “casual tone”.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

直率化
---

Definition of “straightforward tone”: “Being straightforward means writing in a clear and honest manner without any ambiguity, deception, or hidden meanings. It is a way of expressing oneself directly and without any beating around the bush. A straightforward approach to writing involves being clear and concise in what you write, and avoiding the use of unnecessarily complicated or technical language that may be difficult for others to understand. It also involves being honest and transparent in your interactions, and not withholding information or misrepresenting the truth. A straightforward approach can be identified by a number of verbal and nonverbal cues, including:

*   Clear and direct language
*   Avoiding euphemisms or indirect statements
*   Writing plainly and using simple vocabulary
*   Being honest and transparent

Overall, being straightforward can help build trust and credibility with others, as it demonstrates a commitment to honesty and integrity in all communications.”

I will give you text content, you will rewrite it and output that in a “straightforward tone”.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

自信化
---

Definition of “confident tone”: “A confident tone is a way of writing that conveys self-assurance, certainty, and conviction in one’s words and ideas. A person writing with a confident tone writes clearly, firmly, and without hesitation, projecting authority and credibility in their message. A confident tone can be identified by a number of verbal and nonverbal cues, including:

*   Assertive and positive word choices
*   Direct and concise statements

Overall, a confident tone communicates a sense of self-assuredness and credibility, which can help establish trust and influence in both personal and professional contexts.”

I will give you text content, you will rewrite it and output that in a “confident tone”.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

友好化
---

Definition of “friendly tone”: “A friendly tone is a way of writing that conveys warmth, kindness, and approachability. A person writing with a friendly tone uses language and intonation that makes the listener feel welcome, comfortable, and at ease. A friendly tone can be identified by a number of verbal and nonverbal cues, including:

*   Pleasant and upbeat vocabulary
*   Positive and encouraging statements

Overall, a friendly tone communicates a sense of openness, friendliness, and a willingness to connect, which can help build positive relationships and rapport in both personal and professional contexts.”

I will give you text content, you will rewrite it and output that in a “friendly tone”.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

简化语句
----

Definition of “simplify language”: “Simplifying language means using clear and concise language that is easy for the intended audience to understand. This involves avoiding overly complex sentence structures, technical jargon, or obscure vocabulary, and using familiar words and straightforward expressions. The goal is to make the text more accessible to a wider audience, ensuring that the message is communicated effectively without causing confusion or misunderstanding. Simplifying language can be particularly important when writing for a general audience or when trying to convey complex information or ideas in a more approachable way. It is essential for writers to strike a balance between simplifying language and maintaining the tone and voice of the text, so that it remains engaging and informative while being easy to read and understand.”

I will give you text content, you will rewrite it to “simply language” of it and output that in an easy-to-understand version of my text.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

改写语句
----

I will give you text content, you will rewrite it and output that in a re-worded version of my text. Reword the text to convey the same meaning using different words and sentence structures. Avoiding plagiarism, improving the flow and readability of the text, and ensuring that the re-written content is unique and original.

Keep the tone the same.

Keep the meaning the same. Make sure the re-written content’s number of characters is exactly the same as the original text’s number of characters. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, re-write the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

概括内容
----

I will give you text content, you will rewrite it and output that in a short summarized version of my text.

Keep the meaning the same. Ensure that the revised content has significantly fewer characters than the original text, and no more than 100 words, the fewer the better.

Only give me the output and nothing else.

Now, using the concepts above, summarize the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

分析关键要点
------

I will give you text content, you will analyze it and output the key takeaways in bullet point format.

Keep the meaning the same. Ensure that the revised content has significantly fewer characters than the original text, and no more than 100 words, the fewer the better.

Only give me the output and nothing else.

Now, using the concepts above, give me the key takeaways from the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

翻译语句
----

I will give you text content, you will rewrite it and translate the text into {{LANGUAGE}}.

Keep the meaning the same. Do not alter the original structure and formatting outlined in any way. Only give me the output and nothing else.

Now, using the concepts above, translate the following text:

""" {{SELECTED\_TEXT}} """

解释内容
----

I will give you text content, you will explain it and output an easy-to-understand explanation. I want you to pretend to explain the text to a middle school student who has no background knowledge or professional knowledge about the text I give you. Your task is to write the highest quality explanation possible, including examples and analogies if necessary.

Only give me the output and nothing else.

Now, using the concepts above, explain the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """

列举我们该朝什么方向行动
------------

I will give you text content, you will find action items from it and output them in bullet point format. Identify only the action items that need the reader to take action, and exclude action items requiring action from anyone other than the reader.

Only give me the output and nothing else.

Now, using the concepts above, find action items from the following text. Respond in {{AI\_OUTPUT\_LANGUAGE}}:

""" {{SELECTED\_TEXT}} """
