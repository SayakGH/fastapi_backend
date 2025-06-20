from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..schemas import BlogContent, BlogContentResponse, db, TokenData
from ..Oauth2 import get_current_user

router=APIRouter(
    prefix="/blog",
    tags=["Blog Content"]
)

@router.get("/", response_description="Get Blog Posts", response_model= List[BlogContentResponse])
async def get_blog_posts(limit: int = 4, orderby: str = "created_at"):
    try:
        blog_posts = await db["blogPost"].find({ "$query": {}, "$orderby": { orderby : -1 } }).to_list(limit)
        return blog_posts
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
@router.get("/{id}", response_description="Get Blog Post", response_model= BlogContentResponse)
async def get_blog_post(id: str):
    try:
        blog_post = await db["blogPost"].find_one({"_id": id})
        return blog_post
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
@router.post(
    "/",
    response_description="Create Post Content",
    response_model=BlogContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    blog_content: BlogContent,
    current_user: TokenData = Depends(get_current_user),
):
    try:
        # 1) Turn Pydantic model into a dict
        print("data", blog_content)
        data = jsonable_encoder(blog_content)
        print("▶ Incoming blog data:", data)

        user = await db["users"].find_one({"_id": current_user.id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Author not found",
            )
        print("▶ Resolved current_user to DB user:", user)

        # 3) Add author info & timestamp
        data["author_name"] = user["name"]
        data["author_id"] = str(user["_id"])
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        print("▶ Final payload for insert:", data)

        # 4) Insert and fetch the new blog post
        result = await db["blogPost"].insert_one(data)
        new_id= result.inserted_id
        created = await db["blogPost"].find_one({"_id": new_id})
        print("▶ Created blog post:", created)
        return created

    except HTTPException:
        # re-raise any HTTPExceptions (404, etc.)
        raise
    except Exception as e:
        print("✘ Unexpected error in create_post:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    
@router.put("/{id}", response_description="Update a blog Post", response_model=BlogContentResponse)
async def update_blog_post(id: str, blog_content: BlogContent, current_user = Depends(get_current_user)):

    if blog_post := await db["blogPost"].find_one({"_id": id}):
        print(blog_post)
        # check if the owner is the currently logged in user
        if blog_post["author_id"] == current_user.id:
            print("owner")
            try:
                blog_content = {k: v for k, v in blog_content.dict().items() if v is not None}

                if len(blog_content) >= 1:
                    update_result = await db["blogPost"].update_one({"_id": id}, {"$set": blog_content})

                    if update_result.modified_count == 1:
                        if (updated_blog_post := await db["blogPost"].find_one({"_id": id})) is not None:
                            return updated_blog_post

                if (existing_blog_post := await db["blogPost"].find_one({"_id": id})) is not None:
                    return existing_blog_post

                raise HTTPException(status_code=404, detail=f"Blog Post {id} not found")

            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
        else:
            raise HTTPException(status_code=403, detail=f"You are not the owner of this blog post")

@router.delete("/{id}", response_description="Delete Blog Post")
async def delete_blog_post(id: str, current_user: TokenData = Depends(get_current_user)):

    # 1) Find the document by string _id
    blog_post = await db["blogPost"].find_one({"_id": id})
    if not blog_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog Post {id} not found"
        )

    # 2) Check that the current user is the author
    if blog_post.get("author_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this blog post"
        )

    # 3) Attempt the delete
    try:
        delete_result = await db["blogPost"].delete_one({"_id": id})
    except Exception as e:
        print("Delete error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    # 4) Return 204 if it actually deleted something
    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT,content=None)

    # 5) If no document was deleted, treat as not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Blog Post {id} not found"
    )