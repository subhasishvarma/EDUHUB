"""
Data Insertion Script for Course Materials
Run this script to add video playlists, notes, and textbooks to your courses.

Usage:
    python add_course_materials.py
"""

from app import create_app
from models import db, Course, CourseVideo, CourseNote, CourseOnlineBook

def add_course_materials():
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting course materials insertion...")
        
        # Course materials data
        course_materials = {
            "Machine Learning": {
                "videos": [
                    {
                        "url": "https://youtube.com/playlist?list=PLKnIA16_Rmvbr7zKYQuBfsVkjoLcJgxHH",
                        "title": "Machine Learning Complete Playlist",
                        "duration": 1200  # Total playlist duration in minutes (estimate)
                    }
                ],
                "notes": [
                    {
                        "url": "https://mrcet.com/downloads/digital_notes/CSE/IV%20Year/MACHINE%20LEARNING(R17A0534).pdf",
                        "title": "Machine Learning Notes - MRCET",
                        "format": "PDF"
                    }
                ],
                "books": [
                    {
                        "url": "https://www.cs.cmu.edu/~tom/files/MachineLearningTomMitchell.pdf",
                        "title": "Machine Learning - Tom Mitchell (CMU)",
                        "page_count": 414
                    }
                ]
            },
            
            "Information Retrieval": {
                "videos": [
                    {
                        "url": "https://youtube.com/playlist?list=PLaZQkZp6WhWwoDuD6pQCmgVyDbUWl_ZUi",
                        "title": "Information Retrieval Complete Playlist",
                        "duration": 900  # Estimate
                    }
                ],
                "notes": [
                    {
                        "url": "https://nlp.stanford.edu/IR-book/information-retrieval-book.html",
                        "title": "Information Retrieval - Stanford NLP",
                        "format": "HTML"
                    }
                ],
                "books": [
                    {
                        "url": "https://nlp.stanford.edu/IR-book/information-retrieval-book.html",
                        "title": "Introduction to Information Retrieval - Stanford",
                        "page_count": 482
                    }
                ]
            },
            
            "Cloud Computing": {
                "videos": [
                    {
                        "url": "https://youtube.com/playlist?list=PLxCzCOWd7aiHRHVUtR-O52MsrdUSrzuy4",
                        "title": "Cloud Computing Complete Course",
                        "duration": 1000  # Estimate
                    }
                ],
                "notes": [
                    {
                        "url": "https://www.scribd.com/document/539915742/Cloud-Computing-Notes",
                        "title": "Cloud Computing Notes",
                        "format": "PDF"
                    }
                ],
                "books": [
                    {
                        "url": "https://mrcet.com/downloads/digital_notes/IT/CLOUD%20COMPUTING%20DIGITAL%20NOTES%20(R18A0523).pdf",
                        "title": "Cloud Computing - MRCET Digital Notes",
                        "page_count": 350
                    }
                ]
            },
            
            "Advanced Algorithms": {
                "videos": [
                    {
                        "url": "https://youtube.com/playlist?list=PLUl4u3cNGP61hsJNdULdudlRL493b-XZf",
                        "title": "MIT Advanced Algorithms",
                        "duration": 1500  # Estimate
                    }
                ],
                "notes": [
                    {
                        "url": "https://mrcet.com/downloads/digital_notes/CSE/Mtech/I%20Year/ADVANCED%20DATA%20STRUCTURES%20AND%20ALGORITHMS.pdf",
                        "title": "Advanced Data Structures and Algorithms - MRCET",
                        "format": "PDF"
                    }
                ],
                "books": [
                    {
                        "url": "https://github.com/calvint/AlgorithmsOneProblems/blob/master/Algorithms/Thomas%20H.%20Cormen,%20Charles%20E.%20Leiserson,%20Ronald%20L.%20Rivest,%20Clifford%20Stein%20Introduction%20to%20Algorithms,%20Third%20Edition%20%202009.pdf",
                        "title": "Introduction to Algorithms - Cormen et al. (CLRS)",
                        "page_count": 1312
                    }
                ]
            }
        }
        
        # Process each course
        for course_name, materials in course_materials.items():
            print(f"\n📚 Processing: {course_name}")
            
            # Find the course
            course = Course.query.filter_by(course_name=course_name).first()
            
            if not course:
                print(f"   ❌ Course '{course_name}' not found in database. Skipping...")
                continue
            
            course_id = course.course_id
            print(f"   ✅ Found course (ID: {course_id})")
            
            # Add videos
            for video_data in materials.get("videos", []):
                existing_video = CourseVideo.query.filter_by(
                    course_id=course_id,
                    video_url=video_data["url"]
                ).first()
                
                if not existing_video:
                    video = CourseVideo(
                        course_id=course_id,
                        video_url=video_data["url"],
                        title=video_data["title"],
                        duration_minutes=video_data["duration"]
                    )
                    db.session.add(video)
                    print(f"   📹 Added video: {video_data['title']}")
                else:
                    print(f"   ⏭️  Video already exists: {video_data['title']}")
            
            # Add notes
            for note_data in materials.get("notes", []):
                existing_note = CourseNote.query.filter_by(
                    course_id=course_id,
                    note_url=note_data["url"]
                ).first()
                
                if not existing_note:
                    note = CourseNote(
                        course_id=course_id,
                        note_url=note_data["url"],
                        title=note_data["title"],
                        format=note_data["format"]
                    )
                    db.session.add(note)
                    print(f"   📄 Added note: {note_data['title']}")
                else:
                    print(f"   ⏭️  Note already exists: {note_data['title']}")
            
            # Add books
            for book_data in materials.get("books", []):
                existing_book = CourseOnlineBook.query.filter_by(
                    course_id=course_id,
                    book_url=book_data["url"]
                ).first()
                
                if not existing_book:
                    book = CourseOnlineBook(
                        course_id=course_id,
                        book_url=book_data["url"],
                        title=book_data["title"],
                        page_count=book_data.get("page_count")
                    )
                    db.session.add(book)
                    print(f"   📖 Added book: {book_data['title']}")
                else:
                    print(f"   ⏭️  Book already exists: {book_data['title']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✅ All course materials added successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            print("Rolling back changes...")


if __name__ == "__main__":
    print("=" * 60)
    print("Course Materials Insertion Script")
    print("=" * 60)
    add_course_materials()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)