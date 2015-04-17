#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################
# Copyright (C) 2014 by codeskyblue
#=============================================

'''
Some snippets of opencv2

## Resize image
ref: <http://docs.opencv.org/modules/imgproc/doc/geometric_transformations.html#void resize(InputArray src, OutputArray dst, Size dsize, double fx, double fy, int interpolation)>

    # half width and height
    small = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)

    # to fixed Size
    small = cv2.resize(image, (100, 50))

## Constant
    1: cv2.IMREAD_COLOR
    0: cv2.IMREAD_GRAYSCALE 
    -1: cv2.IMREAD_UNCHANGED

## Show image
    cv2.imshow('image title',img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

## Generate a blank image
    size = (height, width, channels) = (512, 256, 3)
    img = np.zeros(size, np.uint8)

## Sort points
    pts = [(0, 7), (3, 5), (2, 6)]
    
    sorted(pts, key=lambda p: p[0]) # sort by point x row, expect [(0, 7), (2, 6), (3, 5)]
'''

__version__ = "1.03"
__project_url__ = "https://github.com/netease/aircv"

import cv2
import numpy as np

DEBUG = False

def mark_point(img, (x, y)):
    ''' 调试用的: 标记一个点 '''
    # cv2.rectangle(img, (x, y), (x+10, y+10), 255, 1, lineType=cv2.CV_AA)
    radius = 20
    cv2.circle(img, (x, y), radius, 255, thickness=2)
    cv2.line(img, (x-radius, y), (x+radius, y), 100) # x line
    cv2.line(img, (x, y-radius), (x, y+radius), 100) # y line
    return img

def show(img):
    ''' 显示一个图片 '''
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def imread(filename):
    ''' 
    Like cv2.imread
    This function will make sure filename exists 
    '''
    im = cv2.imread(filename)
    if im is None:
        raise RuntimeError("file: '%s' not exists" % filename)
    return im

def find_template(im_source, im_search, threshold=0.5, rgb=False, bgremove=False):
    '''
    @return find location
    if not found; return None
    '''
    result = find_all_template(im_source, im_search, threshold, 1, rgb, bgremove)
    return result[0] if result else None

def find_all_template(im_source, im_search, threshold=0.5, maxcnt=0, rgb=False, bgremove=False):
    '''
    Locate image position with cv2.templateFind

    Use pixel match to find pictures.

    Args:
        im_source(string): 图像、素材
        im_search(string): 需要查找的图片
        threshold: 阈值，当相识度小于该阈值的时候，就忽略掉

    Returns:
        A tuple of found [(point, score), ...]

    Raises:
        IOError: when file read error
    '''
    # method = cv2.TM_CCORR_NORMED
    # method = cv2.TM_SQDIFF_NORMED
    method = cv2.TM_CCOEFF_NORMED

    if rgb:
        s_bgr = cv2.split(im_search) # Blue Green Red
        i_bgr = cv2.split(im_source)
        weight = (0.3, 0.3, 0.4)
        resbgr = [0, 0, 0]
        for i in range(3): # bgr
            resbgr[i] = cv2.matchTemplate(i_bgr[i], s_bgr[i], method)
        res = resbgr[0]*weight[0] + resbgr[1]*weight[1] + resbgr[2]*weight[2]
    else:
        s_gray = cv2.cvtColor(im_search, cv2.COLOR_BGR2GRAY)
        i_gray = cv2.cvtColor(im_source, cv2.COLOR_BGR2GRAY)
        # 边界提取(来实现背景去除的功能)
        if bgremove:
            s_gray = cv2.Canny(s_gray, 100, 200)
            i_gray = cv2.Canny(i_gray, 100, 200)

        res = cv2.matchTemplate(i_gray, s_gray, method)
    w, h = im_search.shape[1], im_search.shape[0]

    result = []
    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc
        if DEBUG: 
            print 'templmatch_value(thresh:%.1f) = %.3f' %(threshold, max_val) # not show debug
        if max_val < threshold:
            break
        # calculator middle point
        middle_point = (top_left[0]+w/2, top_left[1]+h/2)
        result.append((middle_point, max_val))
        if maxcnt and len(result) >= maxcnt:
            break
        # floodfill the already found area
        cv2.floodFill(res, None, max_loc, (-1000,), max_val-threshold+0.1, 1, flags=cv2.FLOODFILL_FIXED_RANGE)
    return result

sift = cv2.SIFT()

FLANN_INDEX_KDTREE = 0
flann = cv2.FlannBasedMatcher({'algorithm': FLANN_INDEX_KDTREE, 'trees': 5}, dict(checks = 50))

def sift_count(img):
    kp, des = sift.detectAndCompute(img, None)
    return len(kp)

def find_sift(im_source, im_search, min_match_count=10):
    '''
    SIFT特征点匹配
    '''
    return find_all_sift(im_source, im_search, min_match_count, maxcnt=1)
    

def find_all_sift(im_source, im_search, min_match_count=10, maxcnt=0):
    '''
    使用sift算法进行多个相同元素的查找
    Args:
        im_source(string): 图像、素材
        im_search(string): 需要查找的图片
        threshold: 阈值，当相识度小于该阈值的时候，就忽略掉
        maxcnt: 限制匹配的数量

    Returns:
        A tuple of found [(point, rectangle), ...]
        rectangle is a 4 points list
    '''
    kp_sch, des_sch = sift.detectAndCompute(im_search, None)
    if len(kp_sch) < min_match_count:
        return None

    kp_src, des_src = sift.detectAndCompute(im_source, None)
    if len(kp_src) < min_match_count:
        return None

    h, w = im_search.shape[1:]

    result = []
    while True:
        matches = flann.knnMatch(des_sch, des_src, k=2)
        good = []
        for m,n in matches:
            if m.distance < 0.7*n.distance:
                good.append(m)

        if len(good) < min_match_count:
            break

        sch_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        img_pts = np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2) 

        # M是转化矩阵
        M, mask = cv2.findHomography(sch_pts, img_pts, cv2.RANSAC, 5.0)
        # matchesMask = mask.ravel().tolist()

        h, w = im_search.shape[:2]
        pts = np.float32([ [0, 0], [0, h-1], [w-1, h-1], [w-1, 0] ]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        # trans numpy arrary to python list
        # [(a, b), (a1, b1), ...]
        pypts = []
        for npt in dst.astype(int).tolist():
            pypts.append(tuple(npt[0]))

        lt, br = pypts[0], pypts[2]
        middle_point = (lt[0]+w/2, lt[1]+h/2)

        result.append((middle_point, pypts))

        if maxcnt and len(result) >= maxcnt:
            break
        
        # 从特征点中删掉那些已经匹配过的
        qindexes, tindexes = [], []
        for m in good:
            qindexes.append(m.queryIdx) # need to remove from kp_sch
            tindexes.append(m.trainIdx) # need to remove from kp_img

        def filter_index(indexes, arr):
            r = np.ndarray(0, np.float32)
            for i, item in enumerate(arr):
                if i not in qindexes:
                    r = np.append(r, item)
            return r
        # print type(des_sch[0][0])
        kp_sch = filter_index(qindexes, kp_sch)
        des_sch =filter_index(qindexes, des_sch)
        kp_src = filter_index(tindexes, kp_src)
        des_src = filter_index(tindexes, des_src)

    return result

def find_all(im_source, im_search, maxcnt=0):
    '''
    优先SIFT，之后Template
    @ return [(x,y), ...]
    '''
    if sift_count(im_search) >= 20:
        result = find_all_sift(im_source, im_search, maxcnt=maxcnt)
    else:
        result = find_all_template(im_source, im_search, maxcnt=maxcnt)
    if result is None:
        return []
    return [point for point, score in result]

def find(im_source, im_search):
    '''
    Only find maximum one object
    '''
    r = find_all(im_source, im_search, maxcnt=1)
    return r[0] if r else None

def main():
    print cv2.IMREAD_COLOR
    print cv2.IMREAD_GRAYSCALE
    print cv2.IMREAD_UNCHANGED
    imsrc = imread('testdata/1s.png')
    imsch = imread('testdata/1t.png')

    pt = find(imsrc, imsch)
    mark_point(imsrc, pt)
    show(imsrc)
    imsrc = imread('testdata/2s.png')
    imsch = imread('testdata/2t.png')
    result = find_all_template(imsrc, imsch)
    print result
    pts = []
    for pt, score in result:
        mark_point(imsrc, pt)
        pts.append(pt)
    # pts.sort()
    show(imsrc)
    # print pts
    # print sorted(pts, key=lambda p: p[0])
    
    print 'SIFT count=', sift_count(imsch)
    print find_sift(imsrc, imsch)
    print find_all_sift(imsrc, imsch)
    '''
    for i in range(4):
        cv2.line(imsrc, fourpts[i], fourpts[(i+1)%4], (0, 0, 0), 5)
        # print pt.astype(np.int32).tolist()
        # print pt, pt[0][0]
        mark_point(imsrc, fourpts[i])
    # show(imsrc)
    ''' 

if __name__ == '__main__':
    main()
